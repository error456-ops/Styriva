class OutfitCandidateBuilder:

    def __init__(self, outfits, consultation):
        self.outfits = outfits
        self.consultation = consultation

    def build(self):

        return {
            "gender": self.consultation.gender,
            "occasion": self.consultation.occasion,
            "weather": self.consultation.weather,
            "vibe": self.consultation.vibe,
            "outfit_candidates": self.outfits
        }