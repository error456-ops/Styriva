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

    # NEW: Style My Piece
    @staticmethod
    def create_piece_styling_job(
        piece_styling: PieceStyling,
    ):

        existing_job = Job.objects.filter(
            piece_styling=piece_styling,
            job_type=JobType.PIECE_STYLING,
            job_status__in=[
                JobStatus.PENDING,
                JobStatus.RUNNING,
            ],
        ).first()

        if existing_job:
            return existing_job

        return Job.objects.create(
            piece_styling=piece_styling,
            job_type=JobType.PIECE_STYLING,
            payload={
                "number_of_looks": 6,
            },
        )