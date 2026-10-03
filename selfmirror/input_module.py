from .models import StyleConsultation


class InputModule:

    def __init__(self, consultation_id):

        self.consultation = StyleConsultation.objects.get(
            id=consultation_id
        )

    # =====================================================
    # Validation
    # =====================================================

    def check(self):

        required_fields = [

            self.consultation.user_model_photo,

            self.consultation.top_1,
            self.consultation.top_2,
            self.consultation.top_3,

            self.consultation.bottom_1,
            self.consultation.bottom_2,
            self.consultation.bottom_3,
        ]

        for field in required_fields:

            if not field:

                raise ValueError(
                    "Missing image for one of the required fields."
                )

    # =====================================================
    # Build AI Input
    # =====================================================

    def get_data(self):

        self.check()

        data = {

            "gender":
                self.consultation.gender,

            "occasion":
                self.consultation.occasion,

            "vibe":
                self.consultation.vibe,

            "weather":
                self.consultation.weather,

            "user_model_photo":
                self.consultation.user_model_photo.path,

            "top_1":
                self.consultation.top_1.path,

            "top_2":
                self.consultation.top_2.path,

            "top_3":
                self.consultation.top_3.path,

            "bottom_1":
                self.consultation.bottom_1.path,

            "bottom_2":
                self.consultation.bottom_2.path,

            "bottom_3":
                self.consultation.bottom_3.path,
        }

        # ==========================================
        # Optional Shoes (NEW)
        # ==========================================

        if self.consultation.shoe_1:

            data["shoe_1"] = (
                self.consultation.shoe_1.path
            )

        if self.consultation.shoe_2:

            data["shoe_2"] = (
                self.consultation.shoe_2.path
            )

        if self.consultation.shoe_3:

            data["shoe_3"] = (
                self.consultation.shoe_3.path
            )

        # ==========================================
        # Optional Scarves
        # ==========================================

        if self.consultation.scarf_1:

            data["scarf_1"] = (
                self.consultation.scarf_1.path
            )

        if self.consultation.scarf_2:

            data["scarf_2"] = (
                self.consultation.scarf_2.path
            )

        if self.consultation.scarf_3:

            data["scarf_3"] = (
                self.consultation.scarf_3.path
            )

        return data