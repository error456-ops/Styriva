
const CACHE_NAME = "styriva-static-v1";
const OFFLINE_URL = "/offline/";

// INSTALL
self.addEventListener("install", event => {
    event.waitUntil(
        (async () => {
            const cache = await caches.open(CACHE_NAME);
            await cache.add(OFFLINE_URL);
            await self.skipWaiting();
        })()
    );
});

// ACTIVATE
self.addEventListener("activate", event => {
    event.waitUntil(
        (async () => {
            const keys = await caches.keys();

            await Promise.all(
                keys
                    .filter(key =>
                        key.startsWith("styriva-") &&
                        key !== CACHE_NAME
                    )
                    .map(key => caches.delete(key))
            );

            await self.clients.claim();
        })()
    );
});

// FETCH
self.addEventListener("fetch", event => {
    const request = event.request;
    const url = new URL(request.url);

    // Only handle same-origin GET requests
    if (
        request.method !== "GET" ||
        url.origin !== self.location.origin
    ) {
        return;
    }

    // Never intercept sensitive or dynamic sections
    if (
        url.pathname.startsWith("/admin/") ||
        url.pathname.startsWith("/api/") ||
        url.pathname.startsWith("/accounts/") ||
        url.pathname.startsWith("/payments/")
    ) {
        return;
    }

    // Navigation requests: network first, offline fallback
    if (request.mode === "navigate") {
        event.respondWith(
            (async () => {
                try {
                    return await fetch(request);
                } catch (error) {
                    const cachedPage = await caches.match(OFFLINE_URL);

                    return cachedPage || new Response(
                        "STYRIVA is currently offline.",
                        {
                            status: 503,
                            headers: {
                                "Content-Type": "text/plain"
                            }
                        }
                    );
                }
            })()
        );
    }
});
