import base64
import tempfile
import uuid
from contextlib import ExitStack
from pathlib import Path

from django.core.files.base import ContentFile
from openai import OpenAI
from PIL import Image

from media_manager.manager import MediaManager

from .image_utils import local_path


class LookRenderer:
    """
    Generates the final STYRIVA virtual try-on image.

    Responsibilities:
    - Prepare source images for the OpenAI image API.
    - Convert non-PNG images into temporary PNG files.
    - Generate the final styled portrait.
    - Save the generated image through MediaManager.
    - Automatically clean temporary conversion files.

    Supports:
    - One-piece outfits (dress, long frock, gown)
    - Top + bottom, top only, or bottom only
    - Optional shoes and scarf
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

    def _item_path(self, kind):
        """Returns the image path for an outfit slot, or None."""

        item = self.winning_outfit.get(kind)

        if item and item.get("image_path"):
            return item["image_path"]

        return None

    def render(self):

        dress_path = self._item_path("dress")
        top_path = self._item_path("top")
        bottom_path = self._item_path("bottom")
        shoe_path = self._item_path("shoe")
        scarf_path = self._item_path("scarf")

        print("DRESS:", dress_path)
        print("TOP:", top_path)
        print("BOTTOM:", bottom_path)
        print("SHOE:", shoe_path)
        print("SCARF:", scarf_path)

        # Ordered list of the clothing images that will be sent.
        # Image 1 is always the user, then these in order.
        items = []

        if dress_path:

            # A one-piece is the full outfit by itself
            items.append(("one-piece", dress_path))

        else:

            if top_path:
                items.append(("top", top_path))

            if bottom_path:
                items.append(("bottom", bottom_path))

        if shoe_path:
            items.append(("shoes", shoe_path))

        if scarf_path:
            items.append(("scarf", scarf_path))

        if not any(
            kind in ("one-piece", "top", "bottom")
            for kind, _ in items
        ):

            raise ValueError(
                "LookRenderer: the winning outfit has no "
                "top, bottom or one-piece to render."
            )

        return self.generate_tryon(
            self.selfie_path,
            items
        )

    # =====================================================
    # Path Helper
    # =====================================================

    def get_file_path(self, file_or_path):

        # CLOUDINARY: download to a temp file when needed
        return local_path(file_or_path)

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
Only use the clothing from the provided images. Do not add dresses, skirts, or feminine styling elements that were not provided.
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

    def build_prompt(self, items):
        """
        items = ordered list of (kind, path) AFTER the user photo.
        Image 1 is the user. Items start at Image 2.
        """

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

        kinds = [kind for kind, _ in items]

        has_dress = "one-piece" in kinds
        has_top = "top" in kinds
        has_bottom = "bottom" in kinds
        has_shoe = "shoes" in kinds
        has_scarf = "scarf" in kinds

        # -------------------------------------------------
        # Image numbering follows exactly what was sent.
        # -------------------------------------------------

        image_lines = ["1 = user"]
        put_on_lines = []

        for number, kind in enumerate(kinds, start=2):

            image_lines.append(f"{number} = {kind}")

            put_on_lines.append(
                f"the exact {kind} from Image {number}"
            )

        images_text = "\n".join(image_lines)

        put_on_text = ",\n".join(put_on_lines)

        # -------------------------------------------------
        # What is intentionally NOT part of the outfit
        # -------------------------------------------------

        not_included = []

        if has_dress:

            not_included.append(
                "a separate top or bottom (the one-piece is "
                "the complete outfit; do not add anything "
                "under or over it)"
            )

        else:

            if not has_top:
                not_included.append(
                    "a new top (keep the top the person is "
                    "already wearing in Image 1)"
                )

            if not has_bottom:
                not_included.append(
                    "a new bottom (keep the bottom the person is "
                    "already wearing in Image 1)"
                )

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

        # -------------------------------------------------
        # Extra instructions
        # -------------------------------------------------

        extra_lines = []

        if has_dress:
            extra_lines.append(
                "Show the one-piece at its full length, "
                "including the hem, so the whole garment "
                "is visible."
            )

        if has_shoe:
            extra_lines.append(
                "The shoes must be clearly visible and match "
                "the shoe image exactly."
            )

        extra_text = "\n".join(extra_lines)

        return f"""
STYRIVA virtual try-on.

Styling Profile: {self.gender}

{styling_rules}

Edit Image 1.

Do not generate a different person.

{clothing_instruction}

Match every garment exactly.

Do not redesign any clothing.

{extra_text}

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
        items
    ):

        try:

            with tempfile.TemporaryDirectory(
                prefix="styriva_render_"
            ) as temp_directory:

                # Order matters: user first, then the items
                ordered_paths = [selfie_path] + [
                    path for _kind, path in items
                ]

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

                        prompt=self.build_prompt(items),

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