import cv2


class VisionModel:

    def __init__(self, ai_input):
        self.ai_input = ai_input

    def analyze_image(self, image_path, image_type):

        image = cv2.imread(image_path)

        if image is None:
            raise ValueError(
                f"Could not load image: {image_path}"
            )

        gray = cv2.cvtColor(
            image,
            cv2.COLOR_BGR2GRAY
        )

        brightness = gray.mean()

        blur_score = cv2.Laplacian(
            gray,
            cv2.CV_64F
        ).var()

        return {
            "image_path": image_path,
            "image_type": image_type,
            "brightness": round(brightness, 2),
            "blur_score": round(blur_score, 2),
            "height": image.shape[0],
            "width": image.shape[1],
        }

    def analyze(self):

        results = {

            "selfie_analysis":
                self.analyze_image(
                    self.ai_input["user_model_photo"],
                    "selfie"
                ),

            "top_1_analysis":
                self.analyze_image(
                    self.ai_input["top_1"],
                    "top"
                ),

            "top_2_analysis":
                self.analyze_image(
                    self.ai_input["top_2"],
                    "top"
                ),

            "top_3_analysis":
                self.analyze_image(
                    self.ai_input["top_3"],
                    "top"
                ),

            "bottom_1_analysis":
                self.analyze_image(
                    self.ai_input["bottom_1"],
                    "bottom"
                ),

            "bottom_2_analysis":
                self.analyze_image(
                    self.ai_input["bottom_2"],
                    "bottom"
                ),

            "bottom_3_analysis":
                self.analyze_image(
                    self.ai_input["bottom_3"],
                    "bottom"
                ),
        }

        # ==========================================
        # Optional Shoes (NEW)
        # ==========================================

        for key in ("shoe_1", "shoe_2", "shoe_3"):

            if self.ai_input.get(key):

                results[f"{key}_analysis"] = (
                    self.analyze_image(
                        self.ai_input[key],
                        "shoe"
                    )
                )

        # ==========================================
        # Optional Scarves
        # ==========================================

        for key in ("scarf_1", "scarf_2", "scarf_3"):

            if self.ai_input.get(key):

                results[f"{key}_analysis"] = (
                    self.analyze_image(
                        self.ai_input[key],
                        "scarf"
                    )
                )

        return results