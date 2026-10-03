import base64
import tempfile
import uuid
from contextlib import ExitStack
from pathlib import Path

from django.core.files.base import ContentFile
from openai import OpenAI
from PIL import Image

from media_manager.manager import MediaManager


class LookRenderer:
    """
    Generates the final STYRIVA virtual try-on image.

    Responsibilities:
    - Prepare source images for the OpenAI image API.
    - Convert non-PNG images into temporary PNG files.
    - Generate the final styled portrait.
    - Save the generated image through MediaManager.
    - Automatically clean temporary conversion files.
    """

    def __init__(
        self,
        selfie_path,
        winning_outfit,
        styling_result,
        gender
    ):
        self.selfie_path = selfie_path
        self.winning_outfit = winning_outfit
        self.styling_result = styling_result
        self.gender = gender

        self.client = OpenAI()
        self.media_manager = MediaManager()

    # =====================================================
    # Render
    # =====================================================

    def render(self):

        top_path = self.winning_outfit[
            "top"
        ]["image_path"]

        bottom_path = self.winning_outfit[
            "bottom"
        ]["image_path"]

        # NEW: optional shoe
        shoe = self.winning_outfit.get("shoe")
        shoe_path = (
            shoe.get("image_path")
            if shoe and shoe.get("image_path")
            else None
        )

        scarf = self.winning_outfit.get("scarf")
        scarf_path = (
            scarf.get("image_path")
            if scarf and scarf.get("image_path")
            else None
        )

        print("TOP:", top_path)
        print("BOTTOM:", bottom_path)
        print("SHOE:", shoe_path)
        print("SCARF:", scarf_path)

        return self.generate_tryon(
            self.selfie_path,
            top_path,
            bottom_path,
            shoe_path,
            scarf_path
        )

    # =====================================================
    # Path Helper
    # =====================================================

    def get_file_path(self, file_or_path):

        if hasattr(file_or_path, "path"):
            return file_or_path.path

        return str(file_or_path)

    # =====================================================
    # Temporary PNG Conversion
    # =====================================================

    def convert_to_png(
        self,
        image_path,
        temp_directory
    ):

        image_path = self.get_file_path(
            image_path
        )

        source_path = Path(image_path)

        if source_path.suffix.lower() == ".png":
            return str(source_path)

        temporary_filename = (
            f"{uuid.uuid4().hex}.png"
        )

        temporary_path = (
            Path(temp_directory)
            / temporary_filename
        )

        with Image.open(source_path) as image:

            image.save(
                temporary_path,
                format="PNG"
            )

        return str(temporary_path)

    # =====================================================
    # Styling Rules (gender-specific)
    # =====================================================

    def build_styling_rules(self):

        if self.gender == "men":

            return """
Styling rules:

Evaluate the outfit using men's fashion conventions.
Prefer masculine or gender-neutral silhouettes, proportions, and styling.
Consider men's-appropriate layering, color coordination, garment proportions, and overall presentation.
Hair, grooming, and accessories should be appropriate for a man's look.
Do not introduce dresses, skirts, feminine silhouettes, or feminine styling elements.
A scarf may be used only when it genuinely complements the men's outfit and the occasion; otherwise ignore it.
"""

        return """
Styling rules:

Evaluate the outfit using women's fashion conventions.
Consider feminine or gender-neutral silhouettes, proportions, layering, color coordination, and overall presentation.
Hair, makeup, and accessories should be appropriate for a woman's look.
Do not introduce masculine styling elements unless they intentionally fit the requested vibe.
A scarf may be used when it genuinely complements the outfit and occasion.
"""

    # =====================================================
    # Prompt
    # =====================================================

    def build_prompt(self, has_shoe, has_scarf):

        title = self.styling_result.get(
            "title",
            ""
        )

        rationale = self.styling_result.get(
            "styling_rationale",
            ""
        )

        makeup = self.styling_result.get(
            "makeup_recommendation",
            ""
        )

        hair = self.styling_result.get(
            "hair_recommendation",
            ""
        )

        accessories = self.styling_result.get(
            "accessory_recommendation",
            ""
        )

        styling_rules = self.build_styling_rules()

        # -------------------------------------------------
        # Image numbering changes depending on what exists.
        # Order is always: user, top, bottom, [shoe], [scarf]
        # -------------------------------------------------

        image_lines = [
            "1 = user",
            "2 = top",
            "3 = bottom",
        ]

        put_on_lines = [
            "the exact top from Image 2",
            "the exact bottom from Image 3",
        ]

        next_number = 4

        if has_shoe:

            image_lines.append(f"{next_number} = shoes")

            put_on_lines.append(
                f"the exact shoes from Image {next_number}"
            )

            next_number += 1

        if has_scarf:

            image_lines.append(f"{next_number} = scarf")

            put_on_lines.append(
                f"the exact scarf from Image {next_number}"
            )

            next_number += 1

        images_text = "\n".join(image_lines)

        put_on_text = ",\n".join(put_on_lines)

        not_included = []

        if not has_shoe:
            not_included.append(
                "shoes (keep the shoes already in Image 1 "
                "or natural neutral footwear; do not invent "
                "a statement shoe)"
            )

        if not has_scarf:
            not_included.append("a scarf")

        if not_included:

            not_included_text = (
                "The outfit intentionally does NOT include: "
                + "; ".join(not_included)
                + ".\nDo NOT invent or add these items."
            )

        else:

            not_included_text = ""

        clothing_instruction = f"""
Images:
{images_text}

Replace only the clothing.

Put {put_on_text}
onto the person.

{not_included_text}
"""

        shoe_instruction = (
            "The shoes must be clearly visible and match "
            "the shoe image exactly."
            if has_shoe
            else ""
        )

        return f"""
STYRIVA virtual try-on.

Styling Profile: {self.gender}

{styling_rules}

Edit Image 1.

Do not generate a different person.

{clothing_instruction}

Match every garment exactly.

Do not redesign any clothing.

{shoe_instruction}

Keep unchanged:

- face
- body
- pose
- hands
- background
- lighting
- camera angle
- camera distance

Hair:
{hair or "keep as-is"}

Makeup:
{makeup or "natural"}

Accessories:
{accessories or "none"}

Style:
{title}

Reason:
{rationale}

Produce a realistic fashion photograph.

Full body.

Do not crop:

- hair
- feet
- shoes
"""

    # =====================================================
    # Generate Try-On
    # =====================================================

    def generate_tryon(
        self,
        selfie_path,
        top_path,
        bottom_path,
        shoe_path=None,
        scarf_path=None
    ):

        try:

            with tempfile.TemporaryDirectory(
                prefix="styriva_render_"
            ) as temp_directory:

                # Order matters: user, top, bottom, [shoe], [scarf]
                ordered_paths = [
                    selfie_path,
                    top_path,
                    bottom_path,
                ]

                if shoe_path:
                    ordered_paths.append(shoe_path)

                if scarf_path:
                    ordered_paths.append(scarf_path)

                png_paths = [
                    self.convert_to_png(
                        path,
                        temp_directory
                    )
                    for path in ordered_paths
                ]

                for number, png in enumerate(
                    png_paths,
                    start=1
                ):
                    print(f"IMAGE {number} PNG:", png)

                # ExitStack closes every opened file,
                # even if the API call fails.
                with ExitStack() as stack:

                    image_files = [
                        stack.enter_context(open(png, "rb"))
                        for png in png_paths
                    ]

                    response = self.client.images.edit(

                        model="gpt-image-1",

                        image=image_files,

                        prompt=self.build_prompt(
                            has_shoe=shoe_path is not None,
                            has_scarf=scarf_path is not None,
                        ),

                        size="1024x1536",

                        timeout=120,
                    )

            if (
                not response.data
                or not response.data[0].b64_json
            ):

                raise RuntimeError(
                    "LookRenderer received an empty "
                    "image response from OpenAI."
                )

            try:

                image_bytes = base64.b64decode(
                    response.data[0].b64_json
                )

            except Exception as error:

                raise RuntimeError(
                    "LookRenderer could not decode "
                    "the generated image."
                ) from error

            filename = (
                f"generated_{uuid.uuid4().hex}.png"
            )

            storage_path = (
                f"generated_looks/{filename}"
            )

            saved_path = self.media_manager.save(

                storage_path,

                ContentFile(
                    image_bytes,
                    name=filename
                )
            )

            print(
                "GENERATED IMAGE:",
                saved_path
            )

            return saved_path

        except Exception as error:

            print(
                "LookRenderer Error:",
                type(error).__name__,
                str(error)
            )

            raise