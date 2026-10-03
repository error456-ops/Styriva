class OutfitCombination:

    def __init__(self, analysis_data):
        self.analysis_data = analysis_data

    def generate(self):

        outfits = []

        tops = [
            self.analysis_data["top_1_analysis"],
            self.analysis_data["top_2_analysis"],
            self.analysis_data["top_3_analysis"],
        ]

        bottoms = [
            self.analysis_data["bottom_1_analysis"],
            self.analysis_data["bottom_2_analysis"],
            self.analysis_data["bottom_3_analysis"],
        ]

        # ==========================================
        # Optional Shoes (NEW)
        # ==========================================

        shoes = []

        for key in (
            "shoe_1_analysis",
            "shoe_2_analysis",
            "shoe_3_analysis",
        ):

            shoe = self.analysis_data.get(key)

            if shoe:
                shoes.append(shoe)

        # If no shoes were uploaded, use a single "no shoe"
        # option so the old behaviour still works.
        shoe_options = shoes if shoes else [None]

        # ==========================================
        # Optional Scarves
        # ==========================================

        scarves = []

        for key in (
            "scarf_1_analysis",
            "scarf_2_analysis",
            "scarf_3_analysis",
        ):

            scarf = self.analysis_data.get(key)

            if scarf:
                scarves.append(scarf)

        # ==========================================
        # Build combinations
        # ==========================================

        for top in tops:

            for bottom in bottoms:

                for shoe in shoe_options:

                    outfits.append({
                        "top": top,
                        "bottom": bottom,
                        "shoe": shoe,
                        "scarf": None,
                    })

                    for scarf in scarves:

                        outfits.append({
                            "top": top,
                            "bottom": bottom,
                            "shoe": shoe,
                            "scarf": scarf,
                        })

        return outfits