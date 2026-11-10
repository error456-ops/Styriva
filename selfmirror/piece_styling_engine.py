
import base64
import json
import tempfile
from pathlib import Path

from openai import OpenAI
from PIL import Image

from .image_utils import local_path


class PieceStylingEngine:
    """
    Independent, on-demand AI pipeline for Style My Piece.

    Generates exactly ONE look per run().
    Reuses saved garment analysis.
    Supports exactly six free looks.
    """

    NUMBER_OF_LOOKS = 6

    STYLE_PRESETS = [
        {
            "title": "Everyday Chic",
            "description": (
                "A polished everyday outfit with comfortable "
                "pieces and effortless styling."
            ),
        },
        {
            "title": "Office Elegance",
            "description": (
                "A sophisticated professional outfit with "
                "refined tailoring and elegant accessories."
            ),
        },
        {
            "title": "Casual Cool",
            "description": (
                "A relaxed modern outfit with contemporary "
                "casual styling."
            ),
        },
        {
            "title": "Minimal Luxury",
            "description": (
                "A clean, expensive-looking outfit with "
                "minimal accessories and elegant proportions."
            ),
        },
        {
            "title": "Statement Style",
            "description": (
                "A fashionable statement outfit with "
                "interesting layers and distinctive accessories."
            ),
        },
        {
            "title": "Evening Glam",
            "description": (
                "A sophisticated evening outfit with "
                "elevated styling and beautiful accessories."
            ),
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
    # ANALYZE GARMENT
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
Analyze the uploaded clothing item.

Describe only visible details:
- Garment type
- Main color
- Pattern
- Fabric appearance
- Cut and silhouette
- Neckline or collar
- Sleeves or length
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
    # BUILD IMAGE GENERATION PROMPT
    # ==========================================================

    def build_prompt(
        self,
        garment_analysis,
        style
    ):

        occasion = (
            self.piece.occasion
            or "suitable for the selected styling concept"
        )

        preference = (
            self.piece.style_preference
            or "modern and fashionable"
        )

        return f"""
Create a premium, realistic fashion editorial photograph.

THE REFERENCE IMAGE:

The uploaded image contains the exact garment that must
be worn by the fashion model.

GARMENT ANALYSIS:

{json.dumps(garment_analysis, ensure_ascii=False)}

ABSOLUTE GARMENT PRESERVATION RULES:

1. Keep the uploaded garment as the central clothing item.
2. Preserve its original color, pattern, fabric appearance,
   silhouette, cut and distinctive details.
3. Do not replace it with a similar-looking garment.
4. Do not redesign, recolor or alter the garment.
5. Do not invent logos, prints or decorative details.
6. The garment must be clearly visible in the final image.

STYLING CONCEPT:

Title: {style["title"]}

Concept: {style["description"]}

User preference: {preference}

Occasion: {occasion}

Create a complete, coordinated outfit around the uploaded
garment.

You may add suitable complementary clothing, shoes,
bags, jewelry and accessories depending on the garment.

For example:
- A top can be styled with suitable trousers or skirts.
- Bottoms can be styled with a complementary top.
- A dress should remain the main one-piece garment.
- Outerwear should be visibly worn over a suitable outfit.
- Shoes and accessories should complement the garment.

IMPORTANT:

Create an outfit that clearly follows the selected styling
concept. Do not simply reuse the same outfit combination
for every look.

MODEL AND PHOTOGRAPHY:

Show a stylish adult fashion model wearing the outfit.

Use a full-body fashion photograph.

Use natural, realistic proportions and anatomically
correct hands and feet.

Create premium fashion editorial lighting,
a tasteful background and professional composition.

Make the uploaded garment easy to see.

Do not include text, labels, watermarks or collages.

This is one individual styling concept, not a comparison
image or a six-panel collage.

The result should look like a real fashion campaign.
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

            # Get the next requested look.
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

            # STEP 1: Prepare garment image.

            temp_directory, image_path = (
                self.prepare_image()
            )

            # STEP 2: Reuse or create garment analysis.

            garment_analysis = (
                self.get_garment_analysis(
                    image_path
                )
            )

            # STEP 3: Build the selected style prompt.

            print(
                f"Generating look {look_number}/{self.NUMBER_OF_LOOKS}: "
                f"{style['title']}",
                flush=True
            )

            prompt = self.build_prompt(
                garment_analysis,
                style
            )

            # STEP 4: Generate ONE image.

            generated_image = self.generate_image(
                image_path,
                prompt,
                look_number
            )

            print(
                f"Look {look_number} generated successfully.",
                flush=True
            )

            # The dispatcher must save the result first.
            # It should increment next_look_number only
            # after the database save succeeds.

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
