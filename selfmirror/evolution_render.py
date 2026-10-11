import base64
import tempfile
import uuid
from pathlib import Path

from django.core.files.base import ContentFile
from openai import OpenAI
from PIL import Image

from media_manager.manager import MediaManager

from .image_utils import local_path


class EvolutionRenderer:
    """
    STYRIVA Style Evolution Renderer.

    Edits the already-generated STYRIVA portrait while
    preserving identity, pose, background, and the
    winning outfit.

    Responsibilities:
    - Prepare the generated portrait for the image API.
    - Convert non-PNG images into temporary PNG files.
    - Generate the evolved portrait.
    - Save the final image through MediaManager.
    - Automatically clean temporary conversion files.
    """

    def __init__(
        self,
        generated_image,
        styling_result,
        evolution_result
    ):
        self.generated_image = generated_image
        self.styling_result = styling_result
        self.evolution_result = evolution_result

        self.client = OpenAI()
        self.media_manager = MediaManager()

    # =====================================================
    # Path Helper
    # =====================================================

    def get_file_path(self, file_or_path):
        """
        Convert a Django FieldFile or filesystem path
        into a usable local filesystem path.
        """

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
        """
        Convert an image to PNG when necessary.

        The original generated image is never modified.

        If the source is already PNG, its original
        path is returned.

        Otherwise, a temporary PNG is created inside
        this evolution render's temporary directory.
        """

        image_path = self.get_file_path(
            image_path
        )

        source_path = Path(
            image_path
        )

        if source_path.suffix.lower() == ".png":

            return str(
                source_path
            )

        temporary_filename = (
            f"{uuid.uuid4().hex}.png"
        )

        temporary_path = (
            Path(temp_directory)
            / temporary_filename
        )

        with Image.open(
            source_path
        ) as image:

            image.save(
                temporary_path,
                format="PNG"
            )

        return str(
            temporary_path
        )

    # =====================================================
    # Prompt
    # =====================================================

    def _selected(self, field_name):
        """
        Reads a selected_* field from the GeneratedLook.
        getattr keeps old saved looks working.
        """

        return (
            getattr(
                self.styling_result,
                field_name,
                ""
            )
            or ""
        )

    def build_prompt(self):

        added_items = (
            self.evolution_result.get(
                "added_items",
                []
            )
        )

        makeup = (
            self.evolution_result.get(
                "makeup_recommendation",
                ""
            )
        )

        hair = (
            self.evolution_result.get(
                "hair_recommendation",
                ""
            )
        )

        accessories = (
            self.evolution_result.get(
                "accessory_recommendation",
                ""
            )
        )

        reasoning = (
            self.evolution_result.get(
                "reasoning",
                ""
            )
        )

        render_prompt = (
            self.evolution_result.get(
                "render_prompt",
                ""
            )
        )

        # GeneratedLook model fields

        selected_top = self._selected("selected_top")
        selected_bottom = self._selected("selected_bottom")
        selected_dress = self._selected("selected_dress")
        selected_shoe = self._selected("selected_shoe")
        selected_scarf = self._selected("selected_scarf")

        added_items_text = (
            ", ".join(added_items)
            if added_items
            else "none"
        )

        # -------------------------------------------------
        # Describe the outfit that must stay exactly the same
        # -------------------------------------------------

        outfit_lines = []

        if selected_dress:

            outfit_lines.append(
                f"One-piece: {selected_dress}"
            )

            outfit_lines.append(
                "(the one-piece is the complete outfit; "
                "do not add a separate top or bottom)"
            )

        else:

            outfit_lines.append(
                f"Top: {selected_top or 'as already worn'}"
            )

            outfit_lines.append(
                f"Bottom: {selected_bottom or 'as already worn'}"
            )

        outfit_lines.append(
            f"Shoes: {selected_shoe or 'None'}"
        )

        outfit_lines.append(
            f"Scarf: {selected_scarf or 'None'}"
        )

        outfit_text = "\n".join(outfit_lines)

        return f"""
STYRIVA EVOLUTION

Edit the EXISTING portrait.

Do NOT create another person.

Keep unchanged:
- face
- identity
- body
- pose
- lighting
- camera angle
- background
- the shoes (if any are worn)

Keep this outfit EXACTLY:

{outfit_text}

Never replace or redesign the outfit.
Never change the shoes.

Luxury additions:
{added_items_text}

Hair:
{hair or "Keep existing hairstyle"}

Makeup:
{makeup or "Keep existing makeup"}

Accessories:
{accessories or "None"}

Reasoning:
{reasoning}

Extra render notes:
{render_prompt}

Produce a premium fashion photograph.

Keep everything realistic.

No AI artifacts.
"""

    # =====================================================
    # Edit Portrait
    # =====================================================

    def edit_portrait(self):

        try:

            # -------------------------------------------------
            # Create a unique temporary directory for
            # this evolution render.
            #
            # It is automatically deleted after the API call.
            # -------------------------------------------------

            with tempfile.TemporaryDirectory(
                prefix="styriva_evolution_"
            ) as temp_directory:

                portrait = (
                    self.convert_to_png(
                        self.generated_image,
                        temp_directory
                    )
                )

                print(
                    "\n===== STYLE EVOLUTION ====="
                )

                print(
                    "Portrait:",
                    portrait
                )

                # ---------------------------------------------
                # Send existing portrait to OpenAI
                # ---------------------------------------------

                with open(
                    portrait,
                    "rb"
                ) as portrait_f:

                    response = (
                        self.client.images.edit(

                            model="gpt-image-1",

                            image=[
                                portrait_f
                            ],

                            prompt=(
                                self.build_prompt()
                            ),

                            size="1024x1536",

                            timeout=120,
                        )
                    )

            # -------------------------------------------------
            # Validate API response
            # -------------------------------------------------

            if (
                not response.data
                or not response.data[0].b64_json
            ):

                raise RuntimeError(
                    "EvolutionRenderer received "
                    "an empty image response "
                    "from OpenAI."
                )

            # -------------------------------------------------
            # Decode generated image
            # -------------------------------------------------

            try:

                image_bytes = (
                    base64.b64decode(
                        response.data[
                            0
                        ].b64_json
                    )
                )

            except Exception as error:

                raise RuntimeError(
                    "EvolutionRenderer could not "
                    "decode the evolved image."
                ) from error

            # -------------------------------------------------
            # Create unique filename
            # -------------------------------------------------

            filename = (
                f"evolved_"
                f"{uuid.uuid4().hex}.png"
            )

            storage_path = (
                f"evolved_looks/"
                f"{filename}"
            )

            # -------------------------------------------------
            # Save through MediaManager
            # -------------------------------------------------

            saved_path = (
                self.media_manager.save(

                    storage_path,

                    ContentFile(
                        image_bytes,
                        name=filename
                    )
                )
            )

            print(
                "\n===== EVOLUTION COMPLETE ====="
            )

            print(
                "EVOLVED IMAGE:",
                saved_path
            )

            # Return Django storage-relative path.
            #
            # Example:
            # evolved_looks/evolved_xxxxx.png
            return saved_path

        except Exception as error:

            print(
                "\n===== EVOLUTION ERROR ====="
            )

            print(
                type(error).__name__
            )

            print(
                str(error)
            )

            # Propagate failure to StyleEvolution,
            # JobDispatcher, and finally Worker.
            raise

    # =====================================================
    # Render
    # =====================================================

    def render(self):

        return self.edit_portrait()