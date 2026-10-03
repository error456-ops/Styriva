from .evolution_brain import EvolutionBrain
from .evolution_render import EvolutionRenderer


class StyleEvolution:
    """
    Coordinates the complete STYRIVA
    Style Evolution pipeline.

    Flow:

    Existing Generated Portrait
            +
    Existing Styling Result
            +
    User Selected Extras
            +
    Style Preference

            ↓

    Evolution Brain

            ↓

    Evolution Renderer

            ↓

    MediaManager Storage

            ↓

    Evolved Portrait
    """

    def __init__(
        self,
        consultation,
        generated_image,
        styling_result,
        extras,
        style_preference
    ):

        self.consultation = consultation

        self.generated_image = (
            generated_image
        )

        self.styling_result = (
            styling_result
        )

        self.extras = (
            extras
        )

        self.style_preference = (
            style_preference
        )

    # =====================================================
    # Evolve
    # =====================================================

    def evolve(self):

        print(
            "\n=============================="
        )

        print(
            "STYLE EVOLUTION STARTED"
        )

        print(
            "==============================\n"
        )

        # =================================================
        # STEP 1
        # AI decides how to enhance the existing look
        # =================================================

        evolution_brain = (
            EvolutionBrain(

                consultation=(
                    self.consultation
                ),

                styling_result=(
                    self.styling_result
                ),

                extras=(
                    self.extras
                ),

                style_preference=(
                    self.style_preference
                ),
            )
        )

        evolution_result = (
            evolution_brain.generate()
        )

        # -------------------------------------------------
        # Validate Evolution Brain result
        # -------------------------------------------------

        if not evolution_result:

            raise RuntimeError(
                "EvolutionBrain returned no result."
            )

        if not isinstance(
            evolution_result,
            dict
        ):

            raise RuntimeError(
                "EvolutionBrain returned an invalid result."
            )

        print(
            "\nEvolution Brain Finished\n"
        )

        # =================================================
        # STEP 2
        # Modify the existing generated portrait
        # =================================================

        renderer = (
            EvolutionRenderer(

                generated_image=(
                    self.generated_image
                ),

                styling_result=(
                    self.styling_result
                ),

                evolution_result=(
                    evolution_result
                ),
            )
        )

        evolved_image = (
            renderer.render()
        )

        # -------------------------------------------------
        # Never fall back to original generated portrait.
        #
        # EvolutionRenderer should return a MediaManager
        # storage-relative path such as:
        #
        # evolved_looks/evolved_xxxxx.png
        # -------------------------------------------------

        if not evolved_image:

            raise RuntimeError(
                "EvolutionRenderer completed without "
                "returning an evolved image."
            )

        print(
            "\nEvolution Rendering Finished"
        )

        print(
            "Evolved Image:",
            evolved_image
        )

        # =================================================
        # STEP 3
        # Return complete evolution result
        # =================================================

        return {

            "generated_image":
                evolved_image,

            "render_failed":
                False,

            "added_items":
                evolution_result.get(
                    "added_items",
                    []
                ),

            "reasoning":
                evolution_result.get(
                    "reasoning",
                    ""
                ),

            "makeup":
                evolution_result.get(
                    "makeup_recommendation",
                    ""
                ),

            "hair":
                evolution_result.get(
                    "hair_recommendation",
                    ""
                ),

            "accessories":
                evolution_result.get(
                    "accessory_recommendation",
                    ""
                ),

            "render_prompt":
                evolution_result.get(
                    "render_prompt",
                    ""
                ),

            "style_preference":
                self.style_preference,
        }