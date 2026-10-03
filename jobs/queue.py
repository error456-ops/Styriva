from jobs.models import Job
from jobs.constants import JobType, JobStatus
from selfmirror.models import StyleConsultation


class JobQueue:

    @staticmethod
    def create_style_generation_job(
        consultation: StyleConsultation,
    ):

        # ==================================================
        # DUPLICATE JOB PROTECTION
        # ==================================================

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

        # ==================================================
        # CREATE NEW JOB
        # ==================================================

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

        # ==================================================
        # DUPLICATE JOB PROTECTION
        # ==================================================

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

        # ==================================================
        # CREATE NEW JOB
        # ==================================================

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