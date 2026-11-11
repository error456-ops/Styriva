
import base64
import json
import tempfile
from pathlib import Path

from openai import OpenAI
from PIL import Image

from .image_utils import local_path


class PieceStylingEngine:
    """
    Independent AI pipeline for Style My Piece.

    The user uploads ONE fashion item.
    AI creates six different ways to style that exact item.

    This engine does NOT handle Outfit Combination.
    Generates exactly ONE look per run().
    """

    NUMBER_OF_LOOKS = 6

    STYLE_PRESETS = [
        {
            "title": "Everyday Casual",
            "strategy": "casual",
            "description": "Relaxed, practical everyday styling."
        },
        {
            "title": "Elegant Chic",
            "strategy": "elegant",
            "description": "Sophisticated, polished styling."
        },
        {
            "title": "Layered Look",
            "strategy": "layered",
            "description": "Creative layering and visibly different proportions."
        },
        {
            "title": "Minimal Style",
            "strategy": "minimal",
            "description": "Clean, understated styling."
        },
        {
            "title": "Street Style",
            "strategy": "street",
            "description": "Contemporary, fashion-forward styling."
        },
        {
            "title": "Statement Look",
            "strategy": "statement",
            "description": "Bold and distinctive styling."
        },
    ]

    def __init__(self, piece_styling_id):

        from .models import PieceStyling

        self.piece = PieceStyling.objects.get(
            id=piece_styling_id
        )

        self.client = OpenAI()

    # ==========================================================
    # PREPARE GARMENT IMAGE
    # ==========================================================

    def prepare_image(self):

        original_path = local_path(
            self.piece.garment_image
        )

        if not original_path or not Path(original_path).is_file():

            raise FileNotFoundError(
                "Could not access the uploaded garment image."
            )

        temp_directory = tempfile.TemporaryDirectory(
            prefix="styriva_piece_"
        )

        png_path = (
            Path(temp_directory.name) / "garment.png"
        )

        try:

            with Image.open(original_path) as image:

                image = image.convert("RGB")

                image.save(
                    png_path,
                    format="PNG"
                )

        except Exception:

            temp_directory.cleanup()
            raise

        return temp_directory, str(png_path)

    # ==========================================================
    # ANALYZE UPLOADED ITEM
    # ==========================================================

    def analyze_garment(self, image_path):

        with open(image_path, "rb") as image_file:

            encoded_image = base64.b64encode(
                image_file.read()
            ).decode("utf-8")

        response = self.client.chat.completions.create(

            model="gpt-4.1",

            messages=[
                {
                    "role": "user",

                    "content": [
                        {
                            "type": "text",

                            "text": """
Analyze the uploaded fashion item.

Identify the actual item visible in the image.

Describe only visible details:

- Garment or item type
- Main color
- Pattern
- Fabric appearance
- Cut and silhouette
- Neckline or collar, if applicable
- Sleeves or length, if applicable
- Distinctive details

Do not invent details that cannot be seen.

Return valid JSON:

{
    "garment_type": "",
    "color": "",
    "pattern": "",
    "fabric": "",
    "silhouette": "",
    "details": ""
}
"""
                        },
                        {
                            "type": "image_url",

                            "image_url": {
                                "url": (
                                    "data:image/png;base64,"
                                    + encoded_image
                                )
                            },
                        },
                    ],
                }
            ],

            response_format={
                "type": "json_object"
            },

            temperature=0.2,

            max_tokens=400,

            timeout=60,
        )

        raw_result = (
            response.choices[0].message.content
        )

        if not raw_result:

            raise RuntimeError(
                "Garment analysis returned an empty response."
            )

        try:

            result = json.loads(raw_result)

        except json.JSONDecodeError as error:

            raise RuntimeError(
                "Could not read the garment analysis."
            ) from error

        if not isinstance(result, dict):

            raise RuntimeError(
                "Garment analysis must return JSON."
            )

        return result

    # ==========================================================
    # REUSE SAVED GARMENT ANALYSIS
    # ==========================================================

    def get_garment_analysis(self, image_path):

        analysis = self.piece.garment_analysis

        if isinstance(analysis, dict) and analysis:

            print(
                "Using cached garment analysis.",
                flush=True
            )

            return analysis

        print(
            "Analyzing uploaded garment for the first time.",
            flush=True
        )

        analysis = self.analyze_garment(
            image_path
        )

        self.piece.garment_analysis = analysis

        self.piece.save(
            update_fields=["garment_analysis"]
        )

        return analysis

    # ==========================================================
    # IDENTIFY UPLOADED ITEM CATEGORY
    # ==========================================================

    def get_garment_category(self, garment_analysis):

        garment_type = str(
            garment_analysis.get("garment_type", "")
        ).lower().replace("-", " ").strip()

        if any(word in garment_type for word in [
            "dress", "gown", "jumpsuit", "romper"
        ]):
            return "dress"

        if any(word in garment_type for word in [
            "scarf", "shawl", "stole"
        ]):
            return "scarf"

        if any(word in garment_type for word in [
            "shoe", "sneaker", "boot", "heel",
            "sandal", "footwear"
        ]):
            return "shoes"

        if any(word in garment_type for word in [
            "handbag", "bag", "purse"
        ]):
            return "bag"

        if any(word in garment_type for word in [
            "jacket", "coat", "blazer",
            "cardigan", "vest", "outerwear"
        ]):
            return "outerwear"

        if any(word in garment_type for word in [
            "trouser", "pants", "jeans",
            "skirt", "shorts", "leggings"
        ]):
            return "bottom"

        if any(word in garment_type for word in [
            "top", "shirt", "blouse", "t-shirt",
            "tee", "sweater", "sweatshirt",
            "crop top", "tank top"
        ]):
            return "top"

        return "other"

    # ==========================================================
    # GARMENT-SPECIFIC STYLING STRATEGIES
    # ==========================================================

    def get_styling_instruction(self, category, strategy):

        styling_rules = {

            "dress": {

                "casual": """
Keep the exact uploaded dress unchanged.

Style it as a relaxed daytime look.
Use comfortable sneakers or casual flats.
Add a denim jacket or lightweight casual layer.
Use simple everyday accessories.
The result should feel effortless and wearable.
""",

                "elegant": """
Keep the exact uploaded dress unchanged.

Create a sophisticated polished appearance.
Use elegant heels or refined footwear.
Add delicate jewelry and a structured handbag.
If suitable, add a tailored blazer.
Make the result look appropriate for an elegant occasion.
""",

                "layered": """
Keep the exact uploaded dress unchanged.

Make layering the main transformation.
Add a visibly different cardigan, blazer,
cropped jacket or suitable outer layer.
Show the added layer clearly.
Do not hide or replace the dress.
Create interesting fashion proportions.
""",

                "minimal": """
Keep the exact uploaded dress unchanged.

Create a clean, understated appearance.
Use simple footwear, minimal jewelry
and very few accessories.
Focus on elegant proportions and simplicity.
Do not add unnecessary layers.
""",

                "street": """
Keep the exact uploaded dress unchanged.

Create a contemporary street-style appearance.
Use fashionable sneakers or boots.
Add an oversized jacket or modern casual layer.
Use contemporary accessories.
The styling should look youthful and fashion-forward.
""",

                "statement": """
Keep the exact uploaded dress unchanged.

Create a bold fashion-editorial appearance.
Use distinctive footwear, noticeable jewelry
and carefully selected statement accessories.
Make the styling visually striking.
Do not change the original dress.
"""
            },

            "top": {

                "casual": """
Keep the exact uploaded top unchanged.
Pair it with relaxed jeans or casual trousers.
Use sneakers or comfortable flats.
Create a practical everyday appearance.
""",

                "elegant": """
Keep the exact uploaded top unchanged.
Pair it with tailored trousers or a refined skirt.
Use elegant footwear and delicate jewelry.
Create a polished sophisticated appearance.
""",

                "layered": """
Keep the exact uploaded top unchanged.
Add a visibly different blazer, cardigan
or jacket as the main transformation.
Show the layering clearly.
""",

                "minimal": """
Keep the exact uploaded top unchanged.
Pair it with clean, simple neutral bottoms.
Use understated footwear and minimal accessories.
Focus on balanced proportions.
""",

                "street": """
Keep the exact uploaded top unchanged.
Pair it with contemporary wide-leg trousers
or relaxed streetwear bottoms.
Use sneakers and an oversized outer layer.
""",

                "statement": """
Keep the exact uploaded top unchanged.
Pair it with a distinctive skirt or trousers.
Use bold but coordinated footwear and accessories.
Create a striking fashion appearance.
"""
            },

            "bottom": {

                "casual": """
Keep the exact uploaded bottom unchanged.
Pair it with a relaxed everyday top.
Use casual sneakers or flats.
Create a comfortable daytime appearance.
""",

                "elegant": """
Keep the exact uploaded bottom unchanged.
Pair it with a refined blouse or fitted top.
Use elegant footwear and sophisticated accessories.
""",

                "layered": """
Keep the exact uploaded bottom unchanged.
Pair it with a suitable top and a visibly worn
blazer, cardigan or jacket.
Make the layering clear.
""",

                "minimal": """
Keep the exact uploaded bottom unchanged.
Pair it with a simple, clean top.
Use minimal accessories and understated footwear.
""",

                "street": """
Keep the exact uploaded bottom unchanged.
Pair it with a contemporary top or oversized shirt.
Use sneakers and modern streetwear styling.
""",

                "statement": """
Keep the exact uploaded bottom unchanged.
Pair it with a distinctive complementary top.
Use bold footwear and statement accessories.
"""
            },

            "outerwear": {

                "casual": """
Keep the exact uploaded outerwear unchanged
and visibly worn over a relaxed everyday outfit.
Use casual footwear.
""",

                "elegant": """
Keep the exact uploaded outerwear unchanged
and visibly worn over refined tailored clothing.
Use elegant footwear and polished accessories.
""",

                "layered": """
Keep the exact uploaded outerwear unchanged.
Make it the main visible outer layer.
Build a clearly visible layered outfit underneath.
""",

                "minimal": """
Keep the exact uploaded outerwear unchanged.
Wear it over a simple coordinated outfit.
Use minimal accessories.
""",

                "street": """
Keep the exact uploaded outerwear unchanged.
Wear it as the focal point of a modern streetwear look.
Use contemporary footwear and relaxed proportions.
""",

                "statement": """
Keep the exact uploaded outerwear unchanged.
Make it the focal point of a bold fashion look.
Use complementary statement styling.
"""
            },

            "scarf": {

                "casual": """
Keep the exact uploaded scarf unchanged.
Show it casually draped around the neck
with relaxed everyday clothing.
""",

                "elegant": """
Keep the exact uploaded scarf unchanged.
Show an elegant draping technique.
Use refined clothing and sophisticated accessories.
""",

                "layered": """
Keep the exact uploaded scarf unchanged.
Show a creative, clearly visible layered
wrapping or draping technique.
""",

                "minimal": """
Keep the exact uploaded scarf unchanged.
Show a simple, clean and understated draping technique.
Keep the rest of the styling minimal.
""",

                "street": """
Keep the exact uploaded scarf unchanged.
Show a contemporary scarf styling technique
with modern streetwear clothing.
""",

                "statement": """
Keep the exact uploaded scarf unchanged.
Make the scarf visually prominent.
Show a distinctive and creative draping technique.
"""
            },

            "shoes": {

                "casual": """
Keep the exact uploaded shoes unchanged and clearly visible.
Style them with relaxed everyday clothing.
""",

                "elegant": """
Keep the exact uploaded shoes unchanged and clearly visible.
Create a sophisticated outfit that complements them.
""",

                "layered": """
Keep the exact uploaded shoes unchanged and clearly visible.
Create a fashionable outfit with visible clothing layers.
""",

                "minimal": """
Keep the exact uploaded shoes unchanged and clearly visible.
Create a clean, balanced and minimal appearance.
""",

                "street": """
Keep the exact uploaded shoes unchanged and clearly visible.
Build a contemporary streetwear look around them.
""",

                "statement": """
Keep the exact uploaded shoes unchanged and clearly visible.
Create a bold look that makes the shoes stand out.
"""
            },

            "bag": {

                "casual": """
Keep the exact uploaded bag unchanged and clearly visible.
Style it with a relaxed everyday outfit.
""",

                "elegant": """
Keep the exact uploaded bag unchanged and clearly visible.
Create a sophisticated outfit that complements it.
""",

                "layered": """
Keep the exact uploaded bag unchanged and clearly visible.
Create a look with distinct clothing layers.
""",

                "minimal": """
Keep the exact uploaded bag unchanged and clearly visible.
Create a minimal, clean and coordinated appearance.
""",

                "street": """
Keep the exact uploaded bag unchanged and clearly visible.
Create a modern streetwear appearance around it.
""",

                "statement": """
Keep the exact uploaded bag unchanged and clearly visible.
Create a bold appearance that highlights the bag.
"""
            },

            "other": {

                "casual": "Style the exact uploaded item casually.",
                "elegant": "Style the exact uploaded item elegantly.",
                "layered": "Show the exact uploaded item in a visibly layered look.",
                "minimal": "Style the exact uploaded item minimally.",
                "street": "Style the exact uploaded item in a contemporary streetwear look.",
                "statement": "Make the exact uploaded item the focal point of a bold look."
            }
        }

        return styling_rules.get(
            category,
            styling_rules["other"]
        ).get(
            strategy,
            styling_rules["other"]["casual"]
        )

    # ==========================================================
    # BUILD IMAGE GENERATION PROMPT
    # ==========================================================

    def build_prompt(self, garment_analysis, style):

        occasion = (
            self.piece.occasion
            or "suitable for the selected styling concept"
        )

        preference = (
            self.piece.style_preference
            or "modern and fashionable"
        )

        category = self.get_garment_category(
            garment_analysis
        )

        transformation = self.get_styling_instruction(
            category,
            style["strategy"]
        )

        return f"""
You are a professional personal fashion stylist.

YOUR PRODUCT TASK:

This is STYLE MY PIECE.

The user has uploaded ONE fashion item.
Your job is to demonstrate a different way
of wearing, styling or displaying that exact item.

THIS IS NOT OUTFIT COMBINATION GENERATION.

Do not treat this as a request to randomly
create another complete outfit.

UPLOADED ITEM ANALYSIS:

{json.dumps(garment_analysis, ensure_ascii=False)}

DETECTED ITEM CATEGORY:

{category}

ORIGINAL ITEM PRESERVATION:

The reference image contains the exact item
that the user owns.

You MUST preserve:

1. Original color.
2. Original pattern.
3. Fabric appearance.
4. Shape and silhouette.
5. Cut and design.
6. Distinctive visible details.

Never replace the uploaded item.
Never invent a similar substitute.
Never redesign or recolor it.

SELECTED STYLING TRANSFORMATION:

Title: {style["title"]}

Description: {style["description"]}

SPECIFIC INSTRUCTIONS:

{transformation}

USER STYLE PREFERENCE:

{preference}

OCCASION:

{occasion}

VARIATION REQUIREMENTS:

The purpose of this image is to show
a genuinely different styling approach.

Do not rely on changing only a handbag,
jewelry or small accessories.

The selected transformation must be
visually apparent in the final photograph.

For clothing items, change suitable
complementary clothing, layering,
proportions or footwear as instructed.

For dresses, preserve the complete dress
as one garment.

For scarves, show the specified draping.

For shoes and bags, preserve the exact item
and make it clearly visible.

Do not add unnecessary garments.
Do not create an unrelated outfit.

PHOTOGRAPHY:

Create one premium realistic fashion editorial photograph.

Show a stylish adult fashion model
wearing or displaying the exact uploaded item.

Use full-body framing for wearable clothing
when appropriate.

For accessories, frame the model so the
uploaded item is clearly visible.

Use natural body proportions,
realistic anatomy and professional lighting.

Use a tasteful editorial background.

The original uploaded item must be
the most important recognizable element.

OUTPUT:

One individual realistic fashion photograph.

No text.
No labels.
No watermarks.
No collages.
No six-panel layouts.
No comparison images.

Create a visually distinct styling interpretation.
"""

    # ==========================================================
    # GENERATE ONE STYLING IMAGE
    # ==========================================================

    def generate_image(
        self,
        image_path,
        prompt,
        look_number
    ):

        with open(image_path, "rb") as garment_file:

            response = self.client.images.edit(

                model="gpt-image-2.5-sunburst",

                image=[garment_file],

                prompt=prompt,

                size="1024x1536",

                timeout=180,
            )

        if (
            not response.data
            or not response.data[0].b64_json
        ):

            raise RuntimeError(
                f"Image generation failed for look {look_number}."
            )

        try:

            image_bytes = base64.b64decode(
                response.data[0].b64_json
            )

        except Exception as error:

            raise RuntimeError(
                f"Could not decode image {look_number}."
            ) from error

        return image_bytes

    # ==========================================================
    # GENERATE EXACTLY ONE LOOK PER JOB
    # ==========================================================

    def run(self):

        print(
            "===== STYLE MY PIECE: ONE LOOK STARTED =====",
            flush=True
        )

        temp_directory = None

        try:

            # STEP 1: Get next requested look.

            look_number = self.piece.next_look_number

            if (
                look_number < 1
                or look_number > self.NUMBER_OF_LOOKS
            ):

                raise ValueError(
                    f"All {self.NUMBER_OF_LOOKS} Style My Piece looks "
                    "have already been generated."
                )

            style = self.STYLE_PRESETS[
                look_number - 1
            ]

            # STEP 2: Prepare uploaded item.

            temp_directory, image_path = (
                self.prepare_image()
            )

            # STEP 3: Analyze or reuse saved analysis.

            garment_analysis = (
                self.get_garment_analysis(
                    image_path
                )
            )

            # STEP 4: Identify item category.

            category = self.get_garment_category(
                garment_analysis
            )

            print(
                f"Uploaded item category: {category}",
                flush=True
            )

            # STEP 5: Build transformation prompt.

            print(
                f"Generating look {look_number}/{self.NUMBER_OF_LOOKS}: "
                f"{style['title']}",
                flush=True
            )

            prompt = self.build_prompt(
                garment_analysis,
                style
            )

            # STEP 6: Generate ONE image.

            generated_image = self.generate_image(
                image_path,
                prompt,
                look_number
            )

            print(
                f"Look {look_number} generated successfully.",
                flush=True
            )

            # STEP 7: Return result.
            # The dispatcher must save the result first.
            # Increment next_look_number only after
            # the database save succeeds.

            return {
                "look_number": look_number,
                "title": style["title"],
                "description": style["description"],
                "render_prompt": prompt,
                "generated_image": generated_image,
            }

        finally:

            if temp_directory:
                temp_directory.cleanup()
