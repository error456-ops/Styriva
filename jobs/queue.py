
from django.db import transaction

from jobs.models import Job
from jobs.constants import JobType, JobStatus
from selfmirror.models import StyleConsultation, PieceStyling


class JobQueue:

    @staticmethod
    def create_style_generation_job(consultation: StyleConsultation):

        existing_job = Job.objects.filter(
            consultation=consultation,
            job_type=JobType.STYLE_GENERATION,
            job_status__in=[
                JobStatus.PENDING,
                JobStatus.RUNNING,
            ],
        ).first()

        if existing_job:
            return existing_job

        return Job.objects.create(
            consultation=consultation,
            job_type=JobType.STYLE_GENERATION,
            payload={},
        )

    @staticmethod
    def create_style_evolution_job(
        consultation: StyleConsultation,
        style_preference: str,
        extras: list,
    ):

        existing_job = Job.objects.filter(
            consultation=consultation,
            job_type=JobType.STYLE_EVOLUTION,
            job_status__in=[
                JobStatus.PENDING,
                JobStatus.RUNNING,
            ],
        ).first()

        if existing_job:
            return existing_job

        return Job.objects.create(
            consultation=consultation,
            job_type=JobType.STYLE_EVOLUTION,
            payload={
                "style_preference": style_preference,
                "extras": extras,
            },
        )

    @staticmethod
    def create_image_processing_job(
        consultation: StyleConsultation,
        payload=None,
    ):

        return Job.objects.create(
            consultation=consultation,
            job_type=JobType.IMAGE_PROCESSING,
            payload=payload or {},
        )

    # ==========================================================
    # STYLE MY PIECE - ONE LOOK PER JOB
    # ==========================================================

    @staticmethod
    def create_piece_styling_job(
        piece_styling: PieceStyling,
        payload=None,
    ):

        with transaction.atomic():

            # Lock the clothing piece.
            locked_piece = (
                PieceStyling.objects
                .select_for_update()
                .get(pk=piece_styling.pk)
            )

            # Reuse an existing pending or running job.
            existing_job = Job.objects.filter(
                piece_styling=locked_piece,
                job_type=JobType.PIECE_STYLING,
                job_status__in=[
                    JobStatus.PENDING,
                    JobStatus.RUNNING,
                ],
            ).first()

            if existing_job:
                return existing_job

            # Create exactly one look per job.
            return Job.objects.create(
                piece_styling=locked_piece,
                job_type=JobType.PIECE_STYLING,
                payload=payload or {},
            )
