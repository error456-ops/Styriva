from .models import StyleConsultation


class InputModule:

    # Every clothing slot the form can send
    GARMENT_PREFIXES = ("top", "bottom", "dress")
    ACCESSORY_PREFIXES = ("shoe", "scarf")

    def __init__(self, consultation_id):

        self.consultation = StyleConsultation.objects.get(
            id=consultation_id
        )

    # =====================================================
    # Validation
    # =====================================================

    def check(self):

        # The user's own photo is always required
        if not self.consultation.user_model_photo:

            raise ValueError(
                "Missing the user's photo."
            )

        # At least one top, bottom or one-piece is required
        has_garment = any(
            getattr(self.consultation, f"{prefix}_{i}")
            for prefix in self.GARMENT_PREFIXES
            for i in range(1, 4)
        )

        if not has_garment:

            raise ValueError(
                "Please upload at least one top, "
                "bottom or one-piece."
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
                self.consultation.user_model_photo.url,
        }

        # ==========================================
        # Tops, bottoms, one-pieces, shoes, scarves
        # Only the ones the user uploaded are added.
        # ==========================================

        for prefix in (
            self.GARMENT_PREFIXES
            + self.ACCESSORY_PREFIXES
        ):

            for i in range(1, 4):

                field_name = f"{prefix}_{i}"

                field = getattr(
                    self.consultation,
                    field_name
                )

                if field:

                    data[field_name] = field.url

        # ==========================================
        # Helper flags for the next modules
        # ==========================================

        has_top = any(f"top_{i}" in data for i in range(1, 4))
        has_bottom = any(f"bottom_{i}" in data for i in range(1, 4))
        has_dress = any(f"dress_{i}" in data for i in range(1, 4))

        data["has_top"] = has_top
        data["has_bottom"] = has_bottom
        data["has_dress"] = has_dress

        # "onepiece"  -> a dress/frock/gown was uploaded
        # "separates" -> tops and/or bottoms only
        data["outfit_mode"] = (
            "onepiece" if has_dress else "separates"
        )

        return data