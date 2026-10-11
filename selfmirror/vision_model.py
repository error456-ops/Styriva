import cv2

from .image_utils import local_path


class VisionModel:

    # Maps each upload slot to the image type it represents
    ITEM_TYPES = {
        "top": "top",
        "bottom": "bottom",
        "dress": "dress",   # one-piece: dress, long frock, gown
        "shoe": "shoe",
        "scarf": "scarf",
    }

    def __init__(self, ai_input):
        self.ai_input = ai_input

    def analyze_image(self, image_path, image_type):

        image = cv2.imread(local_path(image_path))

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
        }

        # ==========================================
        # Tops, bottoms, one-pieces, shoes, scarves
        # Only the items the user actually uploaded
        # are analyzed. Missing ones are skipped.
        # ==========================================

        for prefix, image_type in self.ITEM_TYPES.items():

            for i in range(1, 4):

                key = f"{prefix}_{i}"

                if self.ai_input.get(key):

                    results[f"{key}_analysis"] = (
                        self.analyze_image(
                            self.ai_input[key],
                            image_type
                        )
                    )

        return results