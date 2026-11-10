import os

from django.conf import settings
from django.core.files.base import File, ContentFile
from django.db import transaction

from jobs.constants import JobType

from selfmirror.ai import StyleEngine
from selfmirror.StyleEvolution import StyleEvolution

from selfmirror.models import (
    GeneratedLook,
    EvolvedLook,
    PieceStyling,
    PieceStylingResult,
)

from selfmirror.piece_styling_engine import PieceStylingEngine

from accounts.services import CreditManager


# ==============================================================
# Cloudinary-compatible file helper
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
    # ==============================================================

    @staticmethod
    def execute(job):

        if job.job_type == JobType.STYLE_GENERATION:

            return JobDispatcher.handle_style_generation(job)

        elif job.job_type == JobType.STYLE_EVOLUTION:

            return JobDispatcher.handle_style_evolution(job)

        elif job.job_type == JobType.IMAGE_PROCESSING:

            return JobDispatcher.handle_image_processing(job)

        elif job.job_type == JobType.PIECE_STYLING:

            return JobDispatcher.handle_piece_styling(job)

        else:

            raise ValueError(
                f"Unknown job type: {job.job_type}"
            )

    # ==========================================================
    # Style Generation - EXISTING PIPELINE
    # ==============================================================

    @staticmethod
    def handle_style_generation(job):

        consultation = job.consultation

        if consultation is None:

            raise ValueError(
                "Style generation job does not "
                "have a consultation."
            )

        engine = StyleEngine(consultation.id)

        result = engine.run()

        if not result:

            raise RuntimeError(
                "StyleEngine returned no result."
            )

        styling_result = result.get("styling_result")
        generated_image = result.get("generated_image")

        if not styling_result:

            raise RuntimeError(
                "StyleEngine returned no styling result."
            )

        if not generated_image:

            raise RuntimeError(
                "Style generation completed without "
                "a generated image."
            )

        generated_look = GeneratedLook.objects.create(

            consultation=consultation,

            selected_top=styling_result.get("selected_top"),

            selected_bottom=styling_result.get("selected_bottom"),

            selected_dress=styling_result.get("selected_dress"),

            selected_shoe=styling_result.get("selected_shoe"),

            selected_scarf=styling_result.get("selected_scarf"),

            title=styling_result.get(
                "title",
                "Generated Look"
            ),

            score=styling_result.get("confidence", 0),

            styling_rationale=styling_result.get("styling_rationale"),

            makeup_recommendation=styling_result.get(
                "makeup_recommendation"
            ),

            hair_recommendation=styling_result.get(
                "hair_recommendation"
            ),

            accessory_recommendation=styling_result.get(
                "accessory_recommendation"
            ),

            render_prompt=styling_result.get("render_prompt"),

            generated_image=to_django_file(
                generated_image,
                "look.png"
            ),
        )

        print("Style Generation completed.")
        print("Generated Look ID:", generated_look.id)

        return generated_look

    # ==========================================================
    # Style Evolution - EXISTING PIPELINE
    # ==============================================================

    @staticmethod
    def handle_style_evolution(job):

        consultation = job.consultation

        generated_look = (
            GeneratedLook.objects
            .filter(consultation=consultation)
            .latest("created_at")
        )

        style_preference = job.payload.get(
            "style_preference",
            ""
        )

        extras = job.payload.get("extras", [])

        engine = StyleEvolution(

            consultation=consultation,

            generated_image=generated_look.generated_image,

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

            added_items=result.get("added_items", []),

            reasoning=result.get("reasoning", ""),

            makeup_recommendation=result.get("makeup", ""),

            hair_recommendation=result.get("hair", ""),

            accessory_recommendation=result.get("accessories", ""),

            render_prompt=result.get("render_prompt", ""),
        )

        evolved.evolved_image = to_django_file(
            result.get("generated_image"),
            "evolved.png"
        )

        evolved.save()

        print("Style Evolution completed.")

        return evolved

    # ==========================================================
    # Image Processing - EXISTING
    # ==============================================================

    @staticmethod
    def handle_image_processing(job):

        raise NotImplementedError(
            "Image Processing worker "
            "is not implemented yet."
        )

    # ==========================================================
    # STYLE MY PIECE - ONE LOOK PER JOB
    # ==============================================================

    @staticmethod
    def handle_piece_styling(job):

        piece = job.piece_styling

        if piece is None:

            raise ValueError(
                "Piece Styling job has no PieceStyling record."
            )

        piece.status = "processing"
        piece.save(update_fields=["status"])

        try:

            # Refresh from database in case an earlier job
            # has already advanced the next look number.
            piece.refresh_from_db()

            look_number = piece.next_look_number

            if look_number > PieceStylingEngine.NUMBER_OF_LOOKS:

                piece.status = "completed"
                piece.save(update_fields=["status"])

                return {
                    "piece_styling_id": piece.id,
                    "status": "completed",
                    "message": "All six looks have already been generated.",
                    "look_number": None,
                }

            # Generate exactly one look.
            engine = PieceStylingEngine(piece.id)
            result = engine.run()

            if not result or not result.get("generated_image"):

                raise RuntimeError(
                    "Piece Styling did not return a generated image."
                )

            if not result.get("title") or not result.get("description"):

                raise RuntimeError(
                    "Piece Styling result is missing its title or description."
                )

            returned_look_number = result.get("look_number")

            if returned_look_number != look_number:

                raise RuntimeError(
                    "The generated look number does not match "
                    "the next expected look number."
                )

            # Save the result and advance the counter together.
            # If the database save fails, the counter is not advanced.
            with transaction.atomic():

                locked_piece = (
                    PieceStyling.objects
                    .select_for_update()
                    .get(pk=piece.pk)
                )

                if locked_piece.next_look_number != look_number:

                    raise RuntimeError(
                        "Another Style My Piece job changed the "
                        "next look number. This result was not saved."
                    )

                PieceStylingResult.objects.create(

                    piece_styling=locked_piece,

                    title=result["title"],

                    description=result["description"],

                    render_prompt=result.get(
                        "render_prompt",
                        ""
                    ),

                    generated_image=to_django_file(
                        result["generated_image"],
                        f"piece_look_{look_number}.png"
                    ),

                    order=look_number,
                )

                locked_piece.next_look_number = look_number + 1
                locked_piece.status = "completed"

                locked_piece.save(
                    update_fields=[
                        "next_look_number",
                        "status",
                    ]
                )

            print(
                f"Style My Piece look {look_number} completed."
            )
            print("Piece Styling ID:", piece.id)
            print(
                f"Looks generated: {piece.results.count()}/"
                f"{PieceStylingEngine.NUMBER_OF_LOOKS}"
            )

            return {
                "piece_styling_id": piece.id,
                "status": "completed",
                "look_number": look_number,
                "title": result["title"],
                "description": result["description"],
                "remaining_looks": max(
                    0,
                    PieceStylingEngine.NUMBER_OF_LOOKS
                    - look_number
                ),
            }

        except Exception:

            piece.status = "failed"

            piece.save(
                update_fields=["status"]
            )

            raise
