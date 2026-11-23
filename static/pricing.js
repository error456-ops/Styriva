/* ==========================================================
        STYRIVA PREMIUM
========================================================== */

document.addEventListener("DOMContentLoaded", () => {

    /* ==========================================
            PRICING PLAN CONFIGURATION
            (must match the plan keys in your Django view)
    ========================================== */

    const allowedPlans = [
        "mini",
        "starter",
        "stylelover",
        "fashionpro"
    ];

    /* ==========================================
            REVEAL ON SCROLL
    ========================================== */

    const reveals = document.querySelectorAll(".reveal");

    function revealElements() {
        const trigger = window.innerHeight * 0.88;

        reveals.forEach(item => {
            if (item.getBoundingClientRect().top < trigger) {
                item.classList.add("active");
            }
        });
    }

    window.addEventListener("scroll", revealElements);
    revealElements();

    /* ==========================================
            FAQ
    ========================================== */

    const faqs = document.querySelectorAll(".faq-item");

    faqs.forEach(faq => {

        const btn = faq.querySelector(".faq-question");
        const answer = faq.querySelector(".faq-answer");
        const icon = faq.querySelector(".faq-icon");

        if (!btn || !answer || !icon) return;

        btn.addEventListener("click", () => {

            faqs.forEach(other => {
                if (other !== faq) {
                    const otherAnswer = other.querySelector(".faq-answer");
                    const otherIcon = other.querySelector(".faq-icon");

                    if (otherAnswer) otherAnswer.style.maxHeight = null;
                    if (otherIcon) otherIcon.textContent = "+";
                }
            });

            if (answer.style.maxHeight) {
                answer.style.maxHeight = null;
                icon.textContent = "+";
            } else {
                answer.style.maxHeight = answer.scrollHeight + "px";
                icon.textContent = "−";
            }

        });

    });

    /* ==========================================
            CREDIT COUNTER HELPERS
    ========================================== */

    const PENDING_KEY = "styriva_pending_payment";

    function getCreditElement() {
        return document.getElementById("credit-count");
    }

    function readCurrentCredits() {
        const el = getCreditElement();
        if (!el) return 0;
        const n = parseInt(el.textContent, 10);
        return isNaN(n) ? 0 : n;
    }

    function setCredits(value) {
        const el = getCreditElement();
        if (el) el.textContent = value + " Credits";
    }

    function clearPending() {
        try {
            sessionStorage.removeItem(PENDING_KEY);
        } catch (e) {}
    }

    /* ==========================================
            AFTER PAYMENT: WAIT FOR CREDITS

            Razorpay sends the browser back to this page.
            If credits are not added yet, keep asking the
            server every 2 seconds until they show up, then
            update the number without a manual refresh.
    ========================================== */

    async function watchPendingPayment() {

        let pending = null;

        try {
            pending = JSON.parse(sessionStorage.getItem(PENDING_KEY));
        } catch (e) {}

        if (!pending) return;

        // Ignore very old flags (older than 10 minutes)
        if (Date.now() - pending.time > 10 * 60 * 1000) {
            clearPending();
            return;
        }

        const el = getCreditElement();
        if (!el) return;

        el.textContent = "Updating credits...";

        for (let i = 0; i < 25; i++) {   // about 50 seconds max

            try {
                const response = await fetch("/payment-status/", {
                    credentials: "same-origin",
                    cache: "no-store"
                });

                if (response.ok) {
                    const data = await response.json();

                    if (data.credits > pending.credits) {
                        setCredits(data.credits);
                        clearPending();
                        return;
                    }
                }
            } catch (e) {
                console.error("Credit check failed:", e);
            }

            await new Promise(resolve => setTimeout(resolve, 2000));
        }

        // Gave up waiting: show the latest number we know and stop
        try {
            const response = await fetch("/payment-status/", {
                credentials: "same-origin",
                cache: "no-store"
            });
            if (response.ok) {
                const data = await response.json();
                setCredits(data.credits);
            }
        } catch (e) {}

        clearPending();
    }

    watchPendingPayment();

    /* ==========================================
            RAZORPAY PAYMENT
    ========================================== */

    const buyButtons = document.querySelectorAll(".buy-btn[data-plan]");

    buyButtons.forEach(button => {

        button.addEventListener("click", async function (event) {

            event.preventDefault();

            const plan = this.dataset.plan;

            if (!allowedPlans.includes(plan)) {
                alert("Invalid pricing plan.");
                console.error("Invalid plan:", plan);
                return;
            }

            if (this.disabled) return;

            this.disabled = true;

            const originalText = this.textContent;
            this.textContent = "Please wait...";

            try {
                await startPayment(plan);
            } finally {
                this.disabled = false;
                this.textContent = originalText;
            }

        });

    });

    /* ==========================================
            CREATE RAZORPAY ORDER

            Redirect mode: after payment, Razorpay sends the
            browser to /payment/callback/. Your server verifies
            and credits the payment, then sends the user back
            here, where watchPendingPayment() above waits for
            the credits to appear.
    ========================================== */

    async function startPayment(plan) {

        try {

            if (typeof Razorpay === "undefined") {
                alert("Payment system failed to load. Please refresh the page and try again.");
                return;
            }

            const csrfToken = getCSRFToken();
            const formData = new FormData();

            formData.append("plan", plan);

            const response = await fetch(
                "/payment/create-order/",
                {
                    method: "POST",
                    headers: {
                        "X-CSRFToken": csrfToken
                    },
                    body: formData
                }
            );

            if (response.status === 403) {
                window.location.href = "/login/";
                return;
            }

            const data = await response.json();

            if (!response.ok || !data.success) {
                alert(data.message || "Unable to start payment.");
                return;
            }

            const options = {

                key: data.key_id,

                amount: data.amount,

                currency: data.currency,

                name: "STYRIVA",

                description: `${data.credits} AI Styling Credits`,

                order_id: data.order_id,

                callback_url: window.location.origin + "/payment/callback/",

                redirect: true,

                modal: {
                    ondismiss: function () {
                        clearPending();
                    }
                },

                theme: {
                    color: "#000000"
                }

            };

            const razorpay = new Razorpay(options);

            razorpay.on("payment.failed", function (response) {

                console.error("Payment failed:", response);

                clearPending();

                alert("Payment failed. Please try again.");

            });

            // Remember how many credits we have right now, so after
            // the redirect we know when the new credits have arrived.
            try {
                sessionStorage.setItem(PENDING_KEY, JSON.stringify({
                    credits: readCurrentCredits(),
                    time: Date.now()
                }));
            } catch (e) {}

            razorpay.open();

        } catch (error) {

            console.error("Payment error:", error);

            clearPending();

            alert("Something went wrong while starting payment.");

        }

    }

    /* ==========================================
            CSRF TOKEN
    ========================================== */

    function getCSRFToken() {

        const cookieValue = document.cookie
            .split("; ")
            .find(row => row.startsWith("csrftoken="));

        if (!cookieValue) return "";

        return decodeURIComponent(
            cookieValue.split("=")[1]
        );

    }

    /* ==========================================
            NAVBAR SCROLL EFFECT
    ========================================== */

    const navbar = document.querySelector(".navbar");

    function updateNavbar() {

        if (!navbar) return;

        if (window.scrollY > 50) {

            navbar.style.background = "rgba(9,9,9,.88)";
            navbar.style.backdropFilter = "blur(24px)";
            navbar.style.borderBottom = "1px solid rgba(255,255,255,.08)";
            navbar.style.boxShadow = "0 10px 35px rgba(0,0,0,.35)";

        } else {

            navbar.style.background = "rgba(9,9,9,.55)";
            navbar.style.backdropFilter = "blur(18px)";
            navbar.style.borderBottom = "1px solid rgba(255,255,255,.05)";
            navbar.style.boxShadow = "none";

        }

    }

    window.addEventListener("scroll", updateNavbar);
    updateNavbar();

    /* ==========================================
            SMOOTH SCROLL
    ========================================== */

    document.querySelectorAll('a[href^="#"]').forEach(anchor => {

        anchor.addEventListener("click", function (event) {

            const href = this.getAttribute("href");

            if (!href || href === "#") return;

            const target = document.querySelector(href);

            if (!target) return;

            event.preventDefault();

            target.scrollIntoView({
                behavior: "smooth",
                block: "start"
            });

        });

    });

    /* ==========================================
            CARD HOVER GLOW
    ========================================== */

    document.querySelectorAll(
        ".pricing-card, .feature-card"
    ).forEach(card => {

        card.addEventListener("mouseenter", () => {
            card.style.boxShadow = "0 30px 70px rgba(201,161,74,.20)";
        });

        card.addEventListener("mouseleave", () => {
            card.style.boxShadow = "";
        });

    });

    /* ==========================================
            HERO IMAGE FLOAT
    ========================================== */

    const heroImage = document.querySelector(".image-card");

    if (heroImage) {

        let direction = 1;

        setInterval(() => {

            heroImage.style.transform =
                direction === 1
                    ? "translateY(-8px)"
                    : "translateY(0px)";

            direction *= -1;

        }, 2500);

    }

    /* ==========================================
            BUTTON SCALE
    ========================================== */

    document.querySelectorAll(".buy-btn").forEach(btn => {

        btn.addEventListener("mouseenter", () => {
            btn.style.transform = "translateY(-4px) scale(1.03)";
        });

        btn.addEventListener("mouseleave", () => {
            btn.style.transform = "";
        });

    });

    /* ==========================================
            ACTIVE NAV LINK
    ========================================== */

    const sections = document.querySelectorAll("section[id]");
    const navLinks = document.querySelectorAll("nav a");

    function updateActiveNav() {

        let current = "";

        sections.forEach(section => {

            const top = window.scrollY;
            const offset = section.offsetTop - 120;
            const height = section.offsetHeight;

            if (top >= offset && top < offset + height) {
                current = section.getAttribute("id");
            }

        });

        navLinks.forEach(link => {

            link.classList.remove("active");

            if (link.getAttribute("href") === "#" + current) {
                link.classList.add("active");
            }

        });

    }

    window.addEventListener("scroll", updateActiveNav);
    updateActiveNav();

});