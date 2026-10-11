class OutfitCombination:

    def __init__(self, analysis_data):
        self.analysis_data = analysis_data

    # ==========================================
    # Collect whichever items were uploaded
    # ==========================================

    def _collect(self, prefix):

        items = []

        for i in range(1, 4):

            item = self.analysis_data.get(
                f"{prefix}_{i}_analysis"
            )

            if item:
                items.append(item)

        return items

    def generate(self):

        outfits = []

        tops = self._collect("top")
        bottoms = self._collect("bottom")
        dresses = self._collect("dress")
        shoes = self._collect("shoe")
        scarves = self._collect("scarf")

        # If no shoes were uploaded, use a single "no shoe"
        # option (the shoes from the person's photo are kept).
        shoe_options = shoes if shoes else [None]

        # ==========================================
        # Base outfits (the main clothing part)
        #
        # - One-piece   -> dress only, no top/bottom
        # - Top+Bottom  -> every top with every bottom
        # - Only tops   -> top, bottom stays as in photo
        # - Only bottoms-> bottom, top stays as in photo
        # ==========================================

        bases = []

        # One-piece outfits
        for dress in dresses:

            bases.append({
                "top": None,
                "bottom": None,
                "dress": dress,
            })

        # Separates
        if tops and bottoms:

            for top in tops:
                for bottom in bottoms:

                    bases.append({
                        "top": top,
                        "bottom": bottom,
                        "dress": None,
                    })

        elif tops:

            for top in tops:

                bases.append({
                    "top": top,
                    "bottom": None,
                    "dress": None,
                })

        elif bottoms:

            for bottom in bottoms:

                bases.append({
                    "top": None,
                    "bottom": bottom,
                    "dress": None,
                })

        # ==========================================
        # Add shoes and scarves to every base outfit
        # ==========================================

        for base in bases:

            for shoe in shoe_options:

                outfits.append({
                    **base,
                    "shoe": shoe,
                    "scarf": None,
                })

                for scarf in scarves:

                    outfits.append({
                        **base,
                        "shoe": shoe,
                        "scarf": scarf,
                    })

        return outfits