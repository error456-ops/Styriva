document.addEventListener("DOMContentLoaded", () => {

    let currentStep = 1;
    const totalSteps = 4;

    const form = document.getElementById("stylist-engine-form");
    const nextBtn = document.getElementById("next-btn");
    const prevBtn = document.getElementById("prev-btn");

    updateSidebar(1);

    /* ==========================================
       NEXT BUTTON
    ========================================== */

    nextBtn.addEventListener("click", () => {

        if (currentStep < totalSteps) {

            const inputName = getInputName(currentStep);

            const input = document.getElementById(
                `input-${inputName}`
            );

            if (input && !input.value) {

                input.focus();

                input.style.borderColor = "#dc2626";

                return;

            }

            // Reset border color once a valid value is chosen
            if (input) {
                input.style.borderColor = "";
            }

            goToStep(currentStep + 1);

            return;

        }

        validateUploads();

    });

    /* ==========================================
       BACK BUTTON
    ========================================== */

    prevBtn.addEventListener("click", () => {

        if (currentStep > 1) {

            goToStep(currentStep - 1);

        }

    });

    /* ==========================================
       STEP NAVIGATION
    ========================================== */

    function goToStep(step) {

        document
            .getElementById(`step-${currentStep}`)
            .classList.replace("step-active", "step-hidden");

        document
            .getElementById(`dot-${currentStep}`)
            .classList.remove("active");

        currentStep = step;

        document
            .getElementById(`step-${currentStep}`)
            .classList.replace("step-hidden", "step-active");

        document
            .getElementById(`dot-${currentStep}`)
            .classList.add("active");

        updateSidebar(currentStep);

        if (currentStep === 1) {

            prevBtn.style.visibility = "hidden";

        } else {

            prevBtn.style.visibility = "visible";

        }

        if (currentStep === totalSteps) {

            nextBtn.innerHTML = "Create My Look ✨";

        } else {

            nextBtn.innerHTML = "Next";

        }

    }

    /* ==========================================
       SIDEBAR
    ========================================== */

    function updateSidebar(step) {

        for (let i = 1; i <= 4; i++) {

            const item = document.getElementById(
                `summary-step-${i}`
            );

            if (!item) continue;

            item.style.color =
                i === step
                    ? "#78350f"
                    : "#9ca3af";

            item.style.fontWeight =
                i === step
                    ? "700"
                    : "500";

        }

    }

    /* ==========================================
       INPUT NAME
    ========================================== */

    function getInputName(step) {

        if (step === 1) return "occasion";

        if (step === 2) return "vibe";

        if (step === 3) return "weather";

        return null;

    }

    /* ==========================================
       FILE VALIDATION
    ========================================== */

    function validateUploads() {

        const required = [

            ["file-user-pic", "Your Photo"],

            ["file-top1", "Top 1"],
            ["file-top2", "Top 2"],
            ["file-top3", "Top 3"],

            ["file-bottom1", "Bottom 1"],
            ["file-bottom2", "Bottom 2"],
            ["file-bottom3", "Bottom 3"],

        ];

        const missing = [];

        required.forEach(item => {

            const input =
                document.getElementById(item[0]);

            if (!input.files.length) {

                missing.push(item[1]);

            }

        });

        if (missing.length > 0) {

            const warning =
                document.getElementById(
                    "capsule-warning"
                );

            const list =
                document.getElementById(
                    "missing-items"
                );

            warning.classList.remove("hidden");

            list.innerHTML = "";

            missing.forEach(item => {

                const div =
                    document.createElement("div");

                div.innerHTML = "• " + item;

                list.appendChild(div);

            });

            warning.scrollIntoView({

                behavior: "smooth"

            });

            return;

        }

        document
            .getElementById("capsule-warning")
            .classList.add("hidden");

        /* ==========================================
           SUBMIT VIA FETCH
           Allows us to intercept a 403 "requires_signup"
           response (e.g. free-trial limit reached) instead
           of letting the browser follow a normal form POST.
        ========================================== */

        fetch(form.action, {
            method: "POST",
            body: new FormData(form),
        })
        .then(async (response) => {

            const data = await response.json();

            // -----------------------------------------
            // Complimentary guest finished
            // -----------------------------------------
            if (response.status === 403 && data.requires_signup) {

                showSignupModal(data.message, data.redirect_url);

                return;

            }

            // -----------------------------------------
            // Premium Upgrade
            // -----------------------------------------
            if (response.status === 403 && data.requires_upgrade) {

                showPremiumModal();

                return;

            }

            // -----------------------------------------
            // Generation started successfully
            // -----------------------------------------
            if (data.success) {

                window.location.href = data.redirect_url;

                return;

            }

            // -----------------------------------------
            // Unexpected server response
            // -----------------------------------------
            alert(
                data.message ||
                "Sorry, we couldn't create your look. Please try again."
            );

        })
        // -----------------------------------------
        // DAILY FREE GENERATION LIMIT
        // (disabled — replaced by the signup-trigger
        // handler above; re-enable this instead of the
        // block above if you want the 2-per-day flow again)
        // -----------------------------------------
        // .then(async (response) => {
        //
        //     const data = await response.json();
        //
        //     if (
        //         response.status === 403 &&
        //         data.daily_limit_reached
        //     ) {
        //
        //         showDailyLimitModal(data.message);
        //
        //         return;
        //
        //     }
        //
        //     if (data.success) {
        //
        //         window.location.href = data.redirect_url;
        //
        //         return;
        //
        //     }
        //
        //     alert(
        //         data.message ||
        //         "Sorry, we couldn't create your look. Please try again."
        //     );
        //
        // })
        .catch((error) => {

            console.error(error);

            alert(
                "We couldn't connect. Please check your internet and try again."
            );

        });

    }

    /* ==========================================
       FILE PREVIEW STATE
    ========================================== */

    function registerUpload(

        fileId,
        textId,
        iconId,
        isPortrait = false,
        defaultText = "",
        defaultIcon = ""

    ) {

        const input =
            document.getElementById(fileId);

        if (!input) return;

        input.addEventListener("change", function () {

            const label =
                this.closest("label");

            if (this.files.length) {

                label.classList.add("completed");

                if (isPortrait) {

                    document.getElementById(
                        textId
                    ).innerHTML =
                        "Photo Uploaded";

                    document.getElementById(
                        iconId
                    ).innerHTML = "📸";

                    document
                        .getElementById(
                            "badge-user-pic"
                        )
                        .innerHTML =
                        "Done ✓";

                } else {

                    document.getElementById(
                        textId
                    ).innerHTML =
                        "Uploaded ✓";

                }

            } else {

                label.classList.remove("completed");

                // Restore original text/icon/badge when file is cleared
                if (isPortrait) {

                    document.getElementById(
                        textId
                    ).innerHTML = defaultText || "Upload your photo";

                    document.getElementById(
                        iconId
                    ).innerHTML = defaultIcon || "👤";

                    document
                        .getElementById(
                            "badge-user-pic"
                        )
                        .innerHTML = "Required";

                } else {

                    document.getElementById(
                        textId
                    ).innerHTML = defaultText;

                }

            }

        });

    }

    /* ==========================================
       REGISTER ALL FILES
    ========================================== */

    registerUpload(
        "file-user-pic",
        "text-user-pic",
        "icon-user-pic",
        true,
        "Upload your photo",
        "👤"
    );

    registerUpload("file-top1", "text-top1", "icon-top1", false, "Top 1");
    registerUpload("file-top2", "text-top2", "icon-top2", false, "Top 2");
    registerUpload("file-top3", "text-top3", "icon-top3", false, "Top 3");

    registerUpload("file-bottom1", "text-bottom1", "icon-bottom1", false, "Bottom 1");
    registerUpload("file-bottom2", "text-bottom2", "icon-bottom2", false, "Bottom 2");
    registerUpload("file-bottom3", "text-bottom3", "icon-bottom3", false, "Bottom 3");

    // Shoes (these were missing before, so they never showed "Uploaded ✓")
    registerUpload("file-shoe1", "text-shoe1", "icon-shoe1", false, "Shoes 1");
    registerUpload("file-shoe2", "text-shoe2", "icon-shoe2", false, "Shoes 2");
    registerUpload("file-shoe3", "text-shoe3", "icon-shoe3", false, "Shoes 3");

    registerUpload("file-scarf1", "text-scarf1", "icon-scarf1", false, "Scarf 1");
    registerUpload("file-scarf2", "text-scarf2", "icon-scarf2", false, "Scarf 2");
    registerUpload("file-scarf3", "text-scarf3", "icon-scarf3", false, "Scarf 3");

    /* ==========================================
       INITIAL STATE
    ========================================== */

    prevBtn.style.visibility = "hidden";

});


const profileButton = document.getElementById("profileButton");
const profileMenu = document.getElementById("profileMenu");

if(profileButton){

    profileButton.addEventListener("click",function(e){

        e.stopPropagation();

        if (profileMenu) profileMenu.classList.toggle("show");

    });

}

document.addEventListener("click",function(){

    // Guard against profileMenu being null (avoids breaking other click handlers)
    if (profileMenu) profileMenu.classList.remove("show");

});

function showSignupModal(message, redirectUrl){

    document.querySelector("#signupModal p").textContent = message;

    document.getElementById("signupBtn").onclick = function () {
        window.location.href = redirectUrl;
    };

    document
        .getElementById("signupModal")
        .classList.add("show");
}

/* ==========================================
   DAILY LIMIT MODAL
   (kept for reference — not currently wired
   into the fetch handler above)
========================================== */

function showDailyLimitModal(message) {

    const modal = document.getElementById("dailyLimitModal");

    if (!modal) {

        alert(
            message ||
            "You've used today's 2 free looks. Come back tomorrow for 2 more."
        );

        return;

    }

    const messageElement = modal.querySelector("p");

    if (messageElement) {

        messageElement.textContent =
            message ||
            "You've used today's 2 free looks. Come back tomorrow for 2 more.";

    }

    modal.classList.add("show");

    document.body.style.overflow = "hidden";

}

function closeDailyLimitModal() {

    const modal = document.getElementById(
        "dailyLimitModal"
    );

    if (!modal) return;

    modal.classList.remove("show");

    document.body.style.overflow = "";

}

/* ==========================================
   PREMIUM MODAL
========================================== */

function showPremiumModal() {

    document
        .getElementById("premiumModal")
        .classList.add("show");

    document.body.style.overflow = "hidden";

}

function closePremiumModal() {

    document
        .getElementById("premiumModal")
        .classList.remove("show");

    document.body.style.overflow = "";

}

const premiumOverlay =
    document.querySelector(".premium-overlay");

if (premiumOverlay) {

    premiumOverlay.addEventListener("click", () => {

        closePremiumModal();

    });

}

document.addEventListener("keydown", function(e){

    if(e.key === "Escape"){

        closePremiumModal();

    }

});

const upgradeBtn = document.getElementById("upgradePremiumButton");

if (upgradeBtn) {

    upgradeBtn.onclick = function () {

        closePremiumModal();

        window.location.href = this.dataset.premiumUrl;

    };

}