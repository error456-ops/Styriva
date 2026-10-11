import os

from django.conf import settings
from django.core.files.base import File, ContentFile

from jobs.constants import JobType

from selfmirror.ai import StyleEngine
from selfmirror.StyleEvolution import StyleEvolution
from selfmirror.models import (
    GeneratedLook,
    EvolvedLook,
)

from accounts.services import CreditManager


# ==============================================================
# Cloudinary helper
#
# Turns bytes, a local file path, or a Django File into something
# Django can upload to Cloudinary through the storage backend.
# ==============================================================

def to_django_file(value, default_name="image.png"):

    if isinstance(value, (bytes, bytearray)):

        return ContentFile(
            bytes(value),
            name=default_name
        )

    if isinstance(value, File):

        return value

    if isinstance(value, str):

        candidates = (
            value,
            os.path.join(settings.MEDIA_ROOT, value),
        )

        for candidate in candidates:

            if os.path.isfile(candidate):

                with open(candidate, "rb") as f:

                    return ContentFile(
                        f.read(),
                        name=os.path.basename(candidate)
                    )

    return value


class JobDispatcher:

    # ==========================================================
    # Job Router
    # ==========================================================

    @staticmethod
    def execute(job):

        if job.job_type == JobType.STYLE_GENERATION:

            return JobDispatcher.handle_style_generation(
                job
            )

        elif job.job_type == JobType.STYLE_EVOLUTION:

            return JobDispatcher.handle_style_evolution(
                job
            )

        elif job.job_type == JobType.IMAGE_PROCESSING:

            return JobDispatcher.handle_image_processing(
                job
            )

        else:

            raise ValueError(
                f"Unknown job type: {job.job_type}"
            )

    # ==========================================================
    # Style Generation
    # ==========================================================

    @staticmethod
    def handle_style_generation(job):

        consultation = job.consultation

        if consultation is None:

            raise ValueError(
                "Style generation job does not "
                "have a consultation."
            )

        # ------------------------------------------------------
        # Run the STYRIVA AI styling pipeline
        # ------------------------------------------------------

        engine = StyleEngine(
            consultation.id
        )

        result = engine.run()

        # ------------------------------------------------------
        # Validate pipeline result
        # ------------------------------------------------------

        if not result:

            raise RuntimeError(
                "StyleEngine returned no result."
            )

        styling_result = result.get(
            "styling_result"
        )

        generated_image = result.get(
            "generated_image"
        )

        if not styling_result:

            raise RuntimeError(
                "StyleEngine returned no styling result."
            )

        if not generated_image:

            raise RuntimeError(
                "Style generation completed without "
                "a generated image."
            )

        # ------------------------------------------------------
        # Save GeneratedLook database record
        # ------------------------------------------------------

        generated_look = GeneratedLook.objects.create(

            consultation=consultation,

            selected_top=styling_result.get(
                "selected_top"
            ),

            selected_bottom=styling_result.get(
                "selected_bottom"
            ),

            # NEW: one-piece (dress, long frock, gown)
            selected_dress=styling_result.get(
                "selected_dress"
            ),

            selected_shoe=styling_result.get(
                "selected_shoe"
            ),

            selected_scarf=styling_result.get(
                "selected_scarf"
            ),

            title=styling_result.get(
                "title",
                "Generated Look"
            ),

            score=styling_result.get(
                "confidence",
                0
            ),

            styling_rationale=styling_result.get(
                "styling_rationale"
            ),

            makeup_recommendation=styling_result.get(
                "makeup_recommendation"
            ),

            hair_recommendation=styling_result.get(
                "hair_recommendation"
            ),

            accessory_recommendation=styling_result.get(
                "accessory_recommendation"
            ),

            render_prompt=styling_result.get(
                "render_prompt"
            ),

            # CLOUDINARY: make sure the image is uploadable
            generated_image=to_django_file(
                generated_image,
                "look.png"
            ),
        )

        # NOTE: the credit is already spent in views.py when the
        # job is created, so it is NOT charged again here.

        print(
            "Style Generation completed."
        )

        print(
            "Generated Look ID:",
            generated_look.id
        )

        return generated_look

    # ==========================================================
    # Style Evolution
    # ==========================================================

    @staticmethod
    def handle_style_evolution(job):

        consultation = job.consultation

        generated_look = (
            GeneratedLook.objects
            .filter(
                consultation=consultation
            )
            .latest(
                "created_at"
            )
        )

        style_preference = job.payload.get(
            "style_preference",
            ""
        )

        extras = job.payload.get(
            "extras",
            []
        )

        engine = StyleEvolution(

            consultation=consultation,

            generated_image=(
                generated_look.generated_image
            ),

            styling_result=generated_look,

            extras=extras,

            style_preference=style_preference,
        )

        result = engine.evolve()

        evolved = EvolvedLook(

            generated_look=generated_look,

            style_preference=result.get(
                "style_preference",
                style_preference
            ),

            selected_extras=extras,

            added_items=result.get(
                "added_items",
                []
            ),

            reasoning=result.get(
                "reasoning",
                ""
            ),

            makeup_recommendation=result.get(
                "makeup",
                ""
            ),

            hair_recommendation=result.get(
                "hair",
                ""
            ),

            accessory_recommendation=result.get(
                "accessories",
                ""
            ),

            render_prompt=result.get(
                "render_prompt",
                ""
            ),
        )

        # CLOUDINARY: make sure the image is uploadable
        evolved.evolved_image = to_django_file(
            result.get("generated_image"),
            "evolved.png"
        )

        evolved.save()

        # NOTE: the credit is already spent in views.py when the
        # job is created, so it is NOT charged again here.

        print(
            "Style Evolution completed."
        )

        return evolved

    # ==========================================================
    # Image Processing
    # ==========================================================

    @staticmethod
    def handle_image_processing(job):

        raise NotImplementedError(
            "Image Processing worker "
            "is not implemented yet."
        )