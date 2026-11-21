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
            PAYMENT STATUS OVERLAY
    ========================================== */

    function showPaymentOverlay(message) {

        let overlay = document.getElementById("payment-overlay");

        if (!overlay) {

            overlay = document.createElement("div");
            overlay.id = "payment-overlay";

            overlay.style.cssText = [
                "position:fixed",
                "inset:0",
                "z-index:99999",
                "display:flex",
                "align-items:center",
                "justify-content:center",
                "background:rgba(0,0,0,.82)",
                "color:#fff",
                "font-family:inherit",
                "text-align:center",
                "padding:24px"
            ].join(";");

            const box = document.createElement("div");
            box.id = "payment-overlay-text";
            box.style.cssText = "max-width:340px;font-size:18px;line-height:1.5;";

            overlay.appendChild(box);
            document.body.appendChild(overlay);
        }

        document.getElementById("payment-overlay-text").textContent = message;
    }

    function hidePaymentOverlay() {

        const overlay = document.getElementById("payment-overlay");

        if (overlay) overlay.remove();

    }

    function updateCreditPill(credits) {

        const pill = document.querySelector(".credit-pill span");

        if (pill && credits !== undefined && credits !== null) {
            pill.textContent = credits + " Credits";
        }

    }

    function sleep(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

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

                handler: function (paymentResponse) {
                    // Show the overlay immediately so the user never
                    // sees a blank or stale page while we confirm.
                    showPaymentOverlay("Confirming your payment…");
                    verifyPayment(paymentResponse);
                },

                theme: {
                    color: "#000000"
                }

            };

            const razorpay = new Razorpay(options);

            razorpay.on("payment.failed", function (response) {

                console.error("Payment failed:", response);

                alert("Payment failed. Please try again.");

            });

            razorpay.open();

        } catch (error) {

            console.error("Payment error:", error);

            alert("Something went wrong while starting payment.");

        }

    }

    /* ==========================================
            VERIFY PAYMENT (with retries)
            Razorpay can take a few seconds to mark a
            payment as captured. We retry instead of
            giving up on the first answer.
    ========================================== */

    async function verifyPayment(paymentResponse) {

        const MAX_ATTEMPTS = 5;
        const WAIT_BETWEEN_MS = 2000;

        for (let attempt = 1; attempt <= MAX_ATTEMPTS; attempt++) {

            try {

                const formData = new FormData();

                formData.append(
                    "razorpay_order_id",
                    paymentResponse.razorpay_order_id
                );

                formData.append(
                    "razorpay_payment_id",
                    paymentResponse.razorpay_payment_id
                );

                formData.append(
                    "razorpay_signature",
                    paymentResponse.razorpay_signature
                );

                const response = await fetch(
                    "/payment/verify/",
                    {
                        method: "POST",
                        headers: {
                            "X-CSRFToken": getCSRFToken()
                        },
                        body: formData
                    }
                );

                let data = {};

                try {
                    data = await response.json();
                } catch (parseError) {
                    data = {};
                }

                // SUCCESS
                if (response.ok && data.success) {

                    updateCreditPill(data.credits);

                    showPaymentOverlay(
                        `Payment successful! You now have ${data.credits} credits.`
                    );

                    await sleep(1500);

                    window.location.reload();

                    return;
                }

                // Only retry when the problem is temporary
                const message = (data.message || "").toLowerCase();

                const isTemporary =
                    response.status >= 500 ||
                    message.includes("captured");

                if (!isTemporary) {

                    hidePaymentOverlay();

                    alert(
                        data.message ||
                        "Payment verification failed. Please contact support if money was deducted."
                    );

                    return;
                }

            } catch (error) {

                // Network problem: try again
                console.error("Verification error (attempt " + attempt + "):", error);

            }

            if (attempt < MAX_ATTEMPTS) {

                showPaymentOverlay("Confirming your payment…");

                await sleep(WAIT_BETWEEN_MS);

            }

        }

        // Still not confirmed. The money is safe: reloading runs the
        // server-side payment sync, which adds the credits.
        showPaymentOverlay(
            "We're still confirming your payment. Your credits will appear in a moment."
        );

        await sleep(3000);

        window.location.reload();

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