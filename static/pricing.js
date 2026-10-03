/* ==========================================================
        STYRIVA PREMIUM
========================================================== */

document.addEventListener("DOMContentLoaded", () => {

    /* ==========================================
            REVEAL ON SCROLL
    ========================================== */

    const reveals = document.querySelectorAll(".reveal");

    function revealElements() {

        const trigger = window.innerHeight * 0.88;

        reveals.forEach(item => {

            const top = item.getBoundingClientRect().top;

            if (top < trigger) {

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

        btn.addEventListener("click", () => {

            faqs.forEach(other => {

                if (other !== faq) {

                    other.querySelector(".faq-answer").style.maxHeight = null;

                    other.querySelector(".faq-icon").textContent = "+";

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
            RAZORPAY PAYMENT
    ========================================== */
    console.log("PAYMENT SECTION LOADED");
    const buyButtons = document.querySelectorAll(".buy-btn[data-plan]")


    buyButtons.forEach(button => {
    button.addEventListener("click", function (event) {
        event.preventDefault();

        const plan = this.dataset.plan;

        console.log("BUY NOW CLICKED:", plan);

        startPayment(plan);
    });
});


    async function startPayment(plan) {

        try {

            const csrfToken = getCSRFToken();

            const formData = new FormData();

            formData.append("plan", plan);

            const response = await fetch(
                "/payment/create-order/",
                {
                    method: "POST",
                    headers: {
                        "X-CSRFToken": csrfToken,
                    },
                    body: formData,
                }
            );

            const data = await response.json();

            if (response.status === 403) {

                window.location.href = "/login/";

                return;
            }

            if (!data.success) {

                alert(
                    data.message ||
                    "Unable to start payment."
                );

                return;
            }

            const options = {

                key: data.key_id,

                amount: data.amount,

                currency: data.currency,

                name: "STYRIVA",

                description:
                    `${data.credits} AI Styling Credits`,

                order_id: data.order_id,

                handler: async function (paymentResponse) {

                    await verifyPayment(paymentResponse);

                },

                theme: {
                    color: "#000000",
                },

            };

            const razorpay = new Razorpay(options);

            razorpay.on(
                "payment.failed",
                function (response) {

                    console.error(
                        "Payment failed:",
                        response
                    );

                    alert(
                        "Payment failed. Please try again."
                    );

                }
            );

            razorpay.open();

        } catch (error) {

            console.error(error);

            alert(
                "Something went wrong while starting payment."
            );

        }

    }


    async function verifyPayment(paymentResponse) {

        try {

            const csrfToken = getCSRFToken();

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
                        "X-CSRFToken": csrfToken,
                    },
                    body: formData,
                }
            );

            const data = await response.json();

            if (!data.success) {

                alert(
                    data.message ||
                    "Payment verification failed."
                );

                return;
            }

            alert(
                `Payment successful! You now have ${data.credits} credits.`
            );

            window.location.reload();

        } catch (error) {

            console.error(error);

            alert(
                "Something went wrong while verifying payment."
            );

        }

    }


    function getCSRFToken() {

        const cookieValue = document.cookie
            .split("; ")
            .find(row => row.startsWith("csrftoken="));

        if (!cookieValue) {
            return "";
        }

        return decodeURIComponent(
            cookieValue.split("=")[1]
        );

    }

});


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

        anchor.addEventListener("click", function(e) {

            const target = document.querySelector(this.getAttribute("href"));

            if (!target) return;

            e.preventDefault();

            target.scrollIntoView({

                behavior: "smooth",

                block: "start"

            });

        });

    });



    /* ==========================================
            CARD HOVER GLOW
    ========================================== */

    document.querySelectorAll(".pricing-card, .feature-card").forEach(card => {

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

    if(heroImage){

        let direction = 1;

        setInterval(() => {

            heroImage.style.transform =

                direction === 1 ?

                "translateY(-8px)" :

                "translateY(0px)";

            direction *= -1;

        },2500);

    }



    /* ==========================================
            BUTTON SCALE
    ========================================== */

    document.querySelectorAll(".buy-btn").forEach(btn=>{

        btn.addEventListener("mouseenter",()=>{

            btn.style.transform="translateY(-4px) scale(1.03)";

        });

        btn.addEventListener("mouseleave",()=>{

            btn.style.transform="";

        });

    });



    /* ==========================================
            ACTIVE NAV LINK
    ========================================== */

    const sections=document.querySelectorAll("section[id]");

    const navLinks=document.querySelectorAll("nav a");

    function updateActiveNav(){

        let current="";

        sections.forEach(section=>{

            const top=window.scrollY;

            const offset=section.offsetTop-120;

            const height=section.offsetHeight;

            if(top>=offset && top<offset+height){

                current=section.getAttribute("id");

            }

        });

        navLinks.forEach(link=>{

            link.classList.remove("active");

            if(link.getAttribute("href")==="#"+current){

                link.classList.add("active");

            }

        });

    }

    window.addEventListener("scroll",updateActiveNav);

    updateActiveNav();