from .input_module import InputModule
from .vision_model import VisionModel
from .outfit_combination import OutfitCombination
from .outfitscorer import OutfitCandidateBuilder
from .brain import AIStylist
from .howtolook import LookRenderer


class StyleEngine:

    def __init__(self, consultation_id):
        self.consultation_id = consultation_id

    def run(self):

        # ==========================
        # Module 1
        # ==========================
        try:
            input_module = InputModule(self.consultation_id)
            ai_input = input_module.get_data()
        except Exception as e:
            raise Exception(f"StyleEngine failed at Module 1 (InputModule): {e}")

        # ==========================
        # Module 2
        # ==========================
        try:
            vision_model = VisionModel(ai_input)
            vision_results = vision_model.analyze()
        except Exception as e:
            raise Exception(f"StyleEngine failed at Module 2 (VisionModel): {e}")

        # ==========================
        # Module 3
        # ==========================
        try:
            outfit_combination = OutfitCombination(vision_results)
            outfit_candidates = outfit_combination.generate()
        except Exception as e:
            raise Exception(f"StyleEngine failed at Module 3 (OutfitCombination): {e}")

        if not outfit_candidates:
            raise Exception(
                "StyleEngine failed at Module 3 (OutfitCombination): "
                "no outfit candidates were generated."
            )

        # ==========================
        # Module 4
        # ==========================
        try:
            candidate_builder = OutfitCandidateBuilder(
                outfit_candidates,
                input_module.consultation
            )
            candidate_package = candidate_builder.build()
        except Exception as e:
            raise Exception(f"StyleEngine failed at Module 4 (OutfitCandidateBuilder): {e}")

        # ==========================
        # Module 5
        # ==========================
        try:
            ai_stylist = AIStylist(candidate_package)
            styling_result = ai_stylist.recommend()
        except Exception as e:
            raise Exception(f"StyleEngine failed at Module 5 (AIStylist): {e}")

        if not styling_result or "winning_outfit" not in styling_result:
            raise Exception(
                "StyleEngine failed at Module 5 (AIStylist): "
                "styling_result is missing 'winning_outfit'."
            )

        # ==========================
        # Module 6
        # ==========================
        try:
            look_renderer = LookRenderer(
                ai_input["user_model_photo"],
                styling_result["winning_outfit"],
                styling_result,
                ai_input["gender"],
            )
            generated_image = look_renderer.render()
        except Exception as e:
            raise Exception(f"StyleEngine failed at Module 6 (LookRenderer): {e}")

        return {
            "styling_result": styling_result,
            "generated_image": generated_image,
            "render_failed": generated_image is None,
        }