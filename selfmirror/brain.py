from openai import OpenAI
from PIL import Image

import base64
import json
import io


class AIStylist:

    # Vision models don't need full-resolution images to judge color/style/fit.
    # Capping the long edge drastically cuts payload size and request latency.
    MAX_EDGE = 512

    def __init__(self, ai_input):
        self.ai_input = ai_input
        self.client = OpenAI()

    def encode_image(self, image_path):
        """
        Resize to a max edge and re-encode as compressed JPEG before
        base64 encoding. Returns (base64_str, mime_type).
        """

        image = Image.open(image_path)

        if image.mode != "RGB":
            image = image.convert("RGB")

        width, height = image.size
        longest_edge = max(width, height)

        if longest_edge > self.MAX_EDGE:
            scale = self.MAX_EDGE / longest_edge
            new_size = (
                int(width * scale),
                int(height * scale)
            )

            image = image.resize(
                new_size,
                Image.LANCZOS
            )

        buffer = io.BytesIO()

        image.save(
            buffer,
            format="JPEG",
            quality=80,
            optimize=True,
        )

        encoded = base64.b64encode(
            buffer.getvalue()
        ).decode("utf-8")

        return encoded, "image/jpeg"

    def get_gender(self):
        """
        Normalizes the styling profile so comparisons are
        case-insensitive and missing values don't crash the prompt.
        """

        gender = self.ai_input.get("gender", "") or ""

        return gender.strip().lower()

    # ======================================================
    # Catalog: send each unique image ONCE, then describe
    # every outfit candidate using item labels (NEW)
    # ======================================================

    def build_catalog(self, outfit_candidates):

        labels = {}
        counters = {
            "top": 0,
            "bottom": 0,
            "shoe": 0,
            "scarf": 0,
        }

        items = []
        candidate_lines = []

        for index, outfit in enumerate(
            outfit_candidates,
            start=1
        ):

            parts = []

            for kind in ("top", "bottom", "shoe", "scarf"):

                item = outfit.get(kind)

                if not item:
                    continue

                path = item["image_path"]

                if path not in labels:

                    counters[kind] += 1

                    labels[path] = (
                        f"{kind.title()} {counters[kind]}"
                    )

                    items.append((labels[path], path))

                parts.append(labels[path])

            candidate_lines.append(
                f"Outfit Candidate {index}: "
                + ", ".join(parts)
            )

        return items, candidate_lines

    def build_prompt(self):

        gender = self.get_gender()

        if gender == "men":

            styling_rules = """
Styling rules:

- Use men's fashion conventions for silhouette, proportions, grooming, and accessories.
- Keep the styling masculine or gender-neutral unless the requested vibe intentionally calls for something different.
- Do not introduce dresses, skirts, feminine silhouettes, or feminine styling elements.
- A scarf may be selected only when it genuinely improves the outfit and suits the occasion.
- For makeup_recommendation, return an empty string unless a subtle grooming-related recommendation is genuinely useful.
- Hair and accessories should be appropriate for the selected men's look.
"""

        elif gender == "women":

            styling_rules = """
Styling rules:

- Use women's fashion conventions for silhouette, proportions, grooming, and accessories.
- Consider feminine or gender-neutral styling according to the requested vibe.
- A scarf may be selected when it genuinely improves the outfit and suits the occasion.
- Provide appropriate makeup, hair, and accessory recommendations when useful.
"""

        else:

            styling_rules = """
Styling rules:

- No specific styling profile was provided.
- Use gender-neutral fashion conventions for silhouette, proportions, grooming, and accessories.
- A scarf may be selected only when it genuinely improves the outfit and suits the occasion.
- Provide makeup, hair, and accessory recommendations only when genuinely useful.
"""

        return f"""
You are STYRIVA, an elite AI Styling Concierge.

Occasion: {self.ai_input['occasion']}
Weather: {self.ai_input['weather']}
Desired Vibe: {self.ai_input['vibe']}
Styling Profile: {gender or "not specified"}

{styling_rules}

You will first be shown labeled clothing item images
(for example "Top 1", "Bottom 2", "Shoe 1", "Scarf 3").
Then you will be given a list of outfit candidates,
each made from those labeled items.

Each outfit candidate contains:
- One Top
- One Bottom
- An OPTIONAL Shoe
- An OPTIONAL Scarf

Some outfit candidates include shoes or a scarf.
Some do not.

If shoes are included, they must suit the occasion,
weather, and vibe, and match the rest of the outfit.
A scarf should ONLY be used if it genuinely improves
the overall outfit.

Evaluate every candidate based on:

- Color harmony
- Style compatibility
- Occasion suitability
- Weather suitability
- Desired vibe
- Overall fashion appeal

Choose the SINGLE BEST outfit.

If the winning outfit does not contain a scarf,
return "selected_scarf" as an empty string.
If the winning outfit does not contain shoes,
return "selected_shoe" as an empty string.

The render_prompt must describe the full winning outfit,
including the shoes if the outfit has them.

Return ONLY valid JSON in exactly this shape:

{{
    "winning_outfit_number": 1,
    "selected_top": "",
    "selected_bottom": "",
    "selected_shoe": "",
    "selected_scarf": "",
    "title": "",
    "confidence": 0,
    "styling_rationale": "",
    "makeup_recommendation": "",
    "hair_recommendation": "",
    "accessory_recommendation": "",
    "render_prompt": ""
}}
"""

    def recommend(self):

        outfit_candidates = self.ai_input["outfit_candidates"]
        num_candidates = len(outfit_candidates)

        items, candidate_lines = self.build_catalog(
            outfit_candidates
        )

        content = [
            {
                "type": "text",
                "text": self.build_prompt(),
            }
        ]

        # ----------------------------
        # Each unique item image, sent once
        # ----------------------------

        for label, image_path in items:

            content.append({
                "type": "text",
                "text": label
            })

            encoded, mime_type = self.encode_image(
                image_path
            )

            content.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:{mime_type};base64,{encoded}"
                }
            })

        # ----------------------------
        # Candidate list (text only)
        # ----------------------------

        content.append({
            "type": "text",
            "text": (
                "Outfit candidates:\n"
                + "\n".join(candidate_lines)
            )
        })

        try:

            response = self.client.chat.completions.create(
                model="gpt-4.1",
                messages=[
                    {
                        "role": "user",
                        "content": content
                    }
                ],
                temperature=0.3,
                max_tokens=800,
                response_format={
                    "type": "json_object"
                },
                timeout=60,
            )

        except Exception as e:

            raise Exception(
                f"AIStylist API call failed: {e}"
            )

        raw = response.choices[0].message.content

        raw = (
            raw.replace("```json", "")
            .replace("```", "")
            .strip()
        )

        try:

            result = json.loads(raw)

        except json.JSONDecodeError:

            raise Exception(
                f"AIStylist returned invalid JSON:\n\n{raw}"
            )

        winner_index = (
            result.get(
                "winning_outfit_number",
                1
            ) - 1
        )

        if not (
            0 <= winner_index < num_candidates
        ):

            raise Exception(
                f"AIStylist returned out-of-range "
                f"winning_outfit_number: "
                f"{result.get('winning_outfit_number')} "
                f"(candidates: {num_candidates})"
            )

        winning_outfit = (
            outfit_candidates[winner_index]
        )

        result["winning_outfit"] = (
            winning_outfit
        )

        # Ensure shoe and scarf are always present in the response
        if "selected_shoe" not in result:
            result["selected_shoe"] = ""

        if "selected_scarf" not in result:
            result["selected_scarf"] = ""

        print("\n===== STYLING RESULT =====")

        print(
            json.dumps(
                result,
                indent=4
            )
        )

        print("==========================\n")

        return result