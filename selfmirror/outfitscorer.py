class OutfitCandidateBuilder:

    def __init__(self, outfits, consultation):
        self.outfits = outfits
        self.consultation = consultation

    # ==========================================
    # Label what kind of outfit this is
    # ==========================================

    @staticmethod
    def _outfit_type(outfit):

        if outfit.get("dress"):
            return "one_piece"

        if outfit.get("top") and outfit.get("bottom"):
            return "top_and_bottom"

        if outfit.get("top"):
            return "top_only"

        if outfit.get("bottom"):
            return "bottom_only"

        return "unknown"

    def build(self):

        candidates = []

        for index, outfit in enumerate(self.outfits):

            candidates.append({
                "candidate_id": index,
                "outfit_type": self._outfit_type(outfit),
                **outfit,
            })

        return {
            "gender": self.consultation.gender,
            "occasion": self.consultation.occasion,
            "weather": self.consultation.weather,
            "vibe": self.consultation.vibe,
            "outfit_candidates": candidates,
        }