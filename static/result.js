/* ==========================================
   STYRIVA RESULT PAGE
   result.js
========================================== */

document.addEventListener("DOMContentLoaded", () => {

    // ==========================
    // Fade In Animation
    // ==========================

    const animatedElements = document.querySelectorAll(
        ".hero, .preview-card, .card, .note-card, .button-wrapper, .evolution-card"
    );

    animatedElements.forEach((element, index) => {
        element.style.opacity = "0";
        element.style.transform = "translateY(30px)";
        element.style.transition = "opacity 0.6s ease, transform 0.6s ease";

        setTimeout(() => {
            element.style.opacity = "1";
            element.style.transform = "translateY(0)";
        }, index * 150);
    });


    // ==========================
    // Download Button Feedback
    // ==========================

    const downloadButton = document.querySelector(".download-btn");

    if (downloadButton) {
        downloadButton.addEventListener("click", () => {
            const originalText = downloadButton.innerHTML;
            downloadButton.innerHTML = "Downloading...";

            setTimeout(() => {
                downloadButton.innerHTML = originalText;
            }, 2000);
        });
    }


    // ==========================
    // Button Hover Scale
    // ==========================

    const buttons = document.querySelectorAll(".primary-btn, .secondary-btn");

    buttons.forEach(button => {
        button.addEventListener("mouseenter", () => {
            button.style.transform = "scale(1.02)";
        });

        button.addEventListener("mouseleave", () => {
            button.style.transform = "scale(1)";
        });
    });


    // ==========================
    // Image Fade In
    // ==========================

    const previewImage = document.querySelector(".preview-image img");

    if (previewImage) {
        previewImage.style.opacity = "1";
    }


    // ==========================
    // Card Hover Shadow
    // ==========================

    const cards = document.querySelectorAll(".card, .preview-card, .note-card");

    cards.forEach(card => {
        card.addEventListener("mouseenter", () => {
            card.style.transition = "all .3s ease";
        });
    });


    // ==========================
    // Smooth Scroll To Top
    // ==========================

    window.scrollTo({
        top: 0,
        behavior: "smooth"
    });

});


/*==================================================
    STYLE EVOLUTION
==================================================*/

document.addEventListener("DOMContentLoaded", () => {

    // ==========================================
    // Elements
    // ==========================================

    const openBtn = document.getElementById("openEvolutionBtn");
    const formSection = document.getElementById("evolutionFormSection");
    const workflow = document.getElementById("evolutionWorkflow");
    const loadingSection = document.getElementById("evolutionLoading");
    const resultSection = document.getElementById("styleEvolutionResult");
    const styleForm = document.getElementById("styleEvolutionForm");
    const loadingTitle = document.querySelector(".loading-card h3");


    // ==========================================
    // Safety Check
    // ==========================================

    if (
        !openBtn ||
        !formSection ||
        !workflow ||
        !loadingSection ||
        !resultSection ||
        !styleForm
    ) {
        console.warn("Style Evolution UI elements are missing.");
        return;
    }


    // ==========================================
    // State
    // ==========================================

    let thinkingInterval = null;
    let evolutionPollingInterval = null;


    // ==========================================
    // Hide Sections Initially
    // ==========================================

    loadingSection.style.display = "none";
    resultSection.style.display = "none";
    formSection.style.display = "none";


    // ==========================================
    // Open Evolution Form
    // ==========================================

    openBtn.addEventListener("click", () => {

        const introSection = document.getElementById("styleEvolutionSection");

        if (introSection) {
            introSection.style.display = "none";
        }

        workflow.style.display = "block";
        formSection.style.display = "block";
        loadingSection.style.display = "none";
        resultSection.style.display = "none";

        workflow.scrollIntoView({
            behavior: "smooth",
            block: "start"
        });

    });


    // ==========================================
    // Handle Form Submission
    // ==========================================

    styleForm.addEventListener("submit", (event) => {

        event.preventDefault();

        formSection.style.display = "none";
        resultSection.style.display = "none";
        loadingSection.style.display = "block";

        startThinkingAnimation();
        generateStyleEvolution();

    });


    // ==========================================
    // Thinking Animation
    // ==========================================

    const thinkingSteps = [
        "Understanding your wardrobe...",
        "Preserving your winning outfit...",
        "Evaluating luxury enhancements...",
        "Matching accessories...",
        "Selecting luxury additions...",
        "Refining hairstyle...",
        "Perfecting makeup...",
        "Generating evolved portrait..."
    ];


    function startThinkingAnimation() {

        if (!loadingTitle) {
            return;
        }

        // Clear old animation if one exists.
        if (thinkingInterval) {
            clearInterval(thinkingInterval);
        }

        let index = 0;

        loadingTitle.innerHTML = thinkingSteps[index];

        thinkingInterval = setInterval(() => {

            index++;

            // Stay on final message while generation continues.
            if (index >= thinkingSteps.length) {

                clearInterval(thinkingInterval);
                thinkingInterval = null;

                loadingTitle.innerHTML = thinkingSteps[thinkingSteps.length - 1];

                return;
            }

            loadingTitle.innerHTML = thinkingSteps[index];

        }, 1800);

    }


    function stopThinkingAnimation() {

        if (thinkingInterval) {
            clearInterval(thinkingInterval);
            thinkingInterval = null;
        }

    }


    // ==========================================
    // Premium Upgrade Modal
    // ==========================================

    function showPremiumModal() {

        console.log("showPremiumModal called");

        const modal = document.getElementById("premiumModal");

        if (!modal) {
            console.error("Premium modal not found.");
            return;
        }

        modal.classList.add("show");
    }

    function closePremiumModal() {

        const modal = document.getElementById("premiumModal");

        if (modal) {
            modal.classList.remove("show");
        }

    }

    // Expose so inline "onclick" handlers (e.g. a
    // close "X" button in the modal markup) can call it.
    window.closePremiumModal = closePremiumModal;


    // ==========================================
    // Main Style Evolution AJAX
    // ==========================================

    async function generateStyleEvolution() {

        try {

            const consultationId = document.getElementById("consultationId").value;

            const csrfTokenElement = document.querySelector("[name=csrfmiddlewaretoken]");

            const selectedStyle = document.querySelector(
                "input[name='style_preference']:checked"
            );

            const checkedExtras = document.querySelectorAll(
                "input[name='extras']:checked"
            );


            // ------------------------------------------
            // Validate required frontend data
            // ------------------------------------------

            if (!consultationId) {
                throw new Error("Consultation ID is missing.");
            }

            if (!csrfTokenElement) {
                throw new Error("Security token is missing.");
            }

            if (!selectedStyle) {
                throw new Error("Please select a styling direction.");
            }

            const csrfToken = csrfTokenElement.value;


            // ------------------------------------------
            // Build FormData
            // ------------------------------------------

            const formData = new FormData();

            formData.append("consultation_id", consultationId);
            formData.append("style_preference", selectedStyle.value);

            checkedExtras.forEach(extra => {
                formData.append("extras[]", extra.value);
            });


            // ------------------------------------------
            // Create Style Evolution Job
            // ------------------------------------------

            const response = await fetch("/style-evolution/", {
                method: "POST",
                headers: {
                    "X-CSRFToken": csrfToken
                },
                body: formData
            });

            const data = await response.json();


            // ------------------------------------------
            // DAILY FREE AI LIMIT
            // Generation + Style Evolution
            // share the same 2-use daily limit.
            // ------------------------------------------

            if (response.status === 403 && data.daily_limit_reached) {

                stopThinkingAnimation();

                loadingSection.style.display = "none";
                formSection.style.display = "block";

                // Use the same modal as normal generation
                if (typeof showDailyLimitModal === "function") {

                    showDailyLimitModal(data.message);

                } else {

                    alert(
                        data.message ||
                        "You've used today's 2 free AI uses. Come back tomorrow for 2 more."
                    );

                }

                return;
            }


            // ------------------------------------------
            // Premium Upgrade Required
            // Keep this for future Premium system.
            // ------------------------------------------

            if (response.status === 403 && data.requires_upgrade) {

                stopThinkingAnimation();

                loadingSection.style.display = "none";
                formSection.style.display = "block";

                showPremiumModal();

                return;
            }


            // ------------------------------------------
            // Backend rejected request
            // ------------------------------------------

            if (!response.ok || !data.success) {
                throw new Error(
                    data.message || "Style Evolution failed to start."
                );
            }


            // ------------------------------------------
            // Start polling background job
            // ------------------------------------------

            pollEvolutionStatus(consultationId);

        }

        catch (error) {

            stopThinkingAnimation();

            loadingSection.style.display = "none";
            formSection.style.display = "block";

            console.error("Style Evolution start error:", error);

        }

    }


    // ==========================================
    // Poll Evolution Status
    // ==========================================

    function pollEvolutionStatus(consultationId) {

        // Prevent duplicate polling loops.
        if (evolutionPollingInterval) {
            clearInterval(evolutionPollingInterval);
        }


        // ------------------------------------------
        // Status checker
        // ------------------------------------------

        async function checkStatus() {

            try {

                const response = await fetch(
                    `/style-evolution-status/${consultationId}/`,
                    { cache: "no-store" }
                );

                if (!response.ok) {
                    throw new Error("Unable to fetch evolution status.");
                }

                const data = await response.json();

                console.log("Evolution Status:", data);


                // ======================================
                // Evolution Completed
                // ======================================

                if (data.completed || data.status === "completed") {

                    stopEvolutionPolling();
                    stopThinkingAnimation();

                    displayEvolutionResult(data);

                    return;
                }


                // ======================================
                // Evolution Failed
                // ======================================

                if (data.status === "failed") {

                    stopEvolutionPolling();
                    stopThinkingAnimation();

                    loadingSection.style.display = "none";
                    formSection.style.display = "block";

                    alert(
                        data.message ||
                        "Style Evolution failed. Please try again."
                    );

                    console.error("Style Evolution failed:", data);

                    return;
                }


                // ======================================
                // Pending
                // ======================================

                if (data.status === "pending") {

                    if (loadingTitle) {
                        loadingTitle.innerHTML = "Waiting for your AI stylist...";
                    }

                    return;
                }


                // ======================================
                // Processing
                // ======================================

                if (data.status === "processing") {
                    // Keep thinking animation running.
                    return;
                }

            }

            catch (error) {

                /*
                Do not immediately stop polling because
                of a temporary network problem.

                The background worker may still be
                successfully processing the job.
                */

                console.error("Evolution polling error:", error);

            }

        }


        // Check immediately.
        checkStatus();

        // Then check every 3 seconds.
        evolutionPollingInterval = setInterval(checkStatus, 3000);

    }


    // ==========================================
    // Stop Evolution Polling
    // ==========================================

    function stopEvolutionPolling() {

        if (evolutionPollingInterval) {
            clearInterval(evolutionPollingInterval);
            evolutionPollingInterval = null;
        }

    }


    // ==========================================
    // Display Evolution Result
    // ==========================================

    function displayEvolutionResult(data) {

        console.log("Evolution Response:", data);

        loadingSection.style.display = "none";
        formSection.style.display = "none";
        resultSection.style.display = "block";


        // --------------------------------------
        // Portrait
        // --------------------------------------

        const portrait = document.getElementById("evolvedPortrait");

        if (!data.generated_image) {

            console.error("generated_image is missing!", data);

            resultSection.style.display = "none";
            formSection.style.display = "block";

            alert("The evolved portrait could not be loaded.");

            return;
        }

        if (portrait) {
            portrait.src = data.generated_image;
        }


        // --------------------------------------
        // Added Items
        // --------------------------------------

        const changes = document.getElementById("evolutionChanges");

        if (changes) {

            changes.innerHTML = "";

            if (data.added_items && data.added_items.length > 0) {

                data.added_items.forEach(item => {
                    const listItem = document.createElement("li");
                    listItem.textContent = `✓ ${item}`;
                    changes.appendChild(listItem);
                });

            } else {

                const listItem = document.createElement("li");
                listItem.textContent = "No additional items were added.";
                changes.appendChild(listItem);

            }

        }


        // --------------------------------------
        // Reasoning
        // --------------------------------------

        const reasoning = document.getElementById("evolutionReasoning");

        if (reasoning) {
            reasoning.textContent = data.reasoning || "";
        }


        // --------------------------------------
        // Scroll To Evolution Result
        // --------------------------------------

        resultSection.scrollIntoView({
            behavior: "smooth",
            block: "start"
        });

    }


    // ==========================================
    // Download Evolution
    // ==========================================

    const downloadEvolutionBtn = document.getElementById("downloadEvolutionBtn");

    if (downloadEvolutionBtn) {

        downloadEvolutionBtn.addEventListener("click", () => {

            const image = document.getElementById("evolvedPortrait");

            if (!image || !image.src) {
                alert("No evolved portrait available.");
                return;
            }

            const link = document.createElement("a");

            link.href = image.src;
            link.download = "style_evolution.png";

            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);

        });

    }


    // ==========================================
    // Compare Button
    // ==========================================

    const compareBtn = document.getElementById("compareLooksBtn");

    if (compareBtn) {

        compareBtn.addEventListener("click", () => {

            window.scrollTo({
                top: 0,
                behavior: "smooth"
            });

        });

    }

});