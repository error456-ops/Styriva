import time

from django.db import transaction
from django.utils import timezone

from jobs.constants import (
    JobStatus,
    JobType,
)
from jobs.models import Job
from jobs.services import JobDispatcher

from accounts.services import CreditManager
from selfmirror.models import PieceStylingResult


class Worker:

    # ==========================================================
    # Start Worker
    # ==========================================================

    def start(self):

        print("Worker started...")

        while True:

            job = self.get_next_job()

            if job is None:

                time.sleep(5)
                continue

            self.process_job(job)

    # ==========================================================
    # Get Next Pending Job
    # ==========================================================

    def get_next_job(self):

        with transaction.atomic():

            job = (
                Job.objects
                .select_for_update(
                    skip_locked=True
                )
                .filter(
                    job_status=JobStatus.PENDING
                )
                .order_by(
                    "created_at"
                )
                .first()
            )

            if job is None:

                return None

            job.job_status = (
                JobStatus.RUNNING
            )

            job.started_at = (
                timezone.now()
            )

            # Clear any previous error.
            job.error_message = ""

            job.save()

            print(
                f"Job {job.id} started. "
                f"Type: {job.job_type}"
            )

            return job

    # ==========================================================
    # Process Job
    # ==========================================================

    def process_job(self, job):

        try:
            JobDispatcher.execute(job)

            job.job_status = JobStatus.COMPLETED
            job.completed_at = timezone.now()
            job.error_message = ""

            print(f"Job {job.id} completed successfully.")

        except Exception as error:

            job.job_status = JobStatus.FAILED
            job.completed_at = timezone.now()

            error_text = str(error).lower()

            if "insufficient_quota" in error_text:
                job.error_message = (
                    "Our AI styling service is temporarily unavailable. "
                    "Please try again in a few minutes."
                )
            elif "timeout" in error_text:
                job.error_message = (
                    "Your styling session took longer than expected. "
                    "Please try again."
                )
            elif "connection" in error_text:
                job.error_message = (
                    "Unable to connect to our AI styling service. "
                    "Please try again."
                )
            else:
                job.error_message = (
                    "Something went wrong while generating "
                    "your personalized look. Please try again later."
                )

            print(f"Job {job.id} failed.")
            print("Error:", type(error).__name__, str(error))

            # --------------------------------------------------
            # Refund a paid Style My Piece look only once.
            # --------------------------------------------------
            if job.job_type == JobType.PIECE_STYLING:

                try:
                    with transaction.atomic():

                        locked_job = (
                            Job.objects
                            .select_for_update()
                            .get(pk=job.pk)
                        )

                        payload = locked_job.payload or {}

                        if (
                            payload.get("credit_charged")
                            and not payload.get("credit_refunded")
                        ):

                            piece = locked_job.piece_styling

                            look_number = payload.get("look_number")

                            result_exists = (
                                PieceStylingResult.objects.filter(
                                    piece_styling=piece,
                                    order=look_number,
                                ).exists()
                            )

                            if not result_exists and piece.user_id:

                                CreditManager.add_credits(
                                    piece.user,
                                    1,
                                )

                                payload["credit_refunded"] = True

                                locked_job.payload = payload
                                locked_job.save(
                                    update_fields=["payload"]
                                )

                                job.payload = payload

                                print(
                                    f"One credit refunded for job {job.id}."
                                )

                except Exception as refund_error:
                    print("Credit refund failed:")
                    print(
                        type(refund_error).__name__,
                        str(refund_error),
                    )

            # --------------------------------------------------
            # Preserve Style Evolution failure handling.
            # --------------------------------------------------
            if job.job_type == JobType.STYLE_EVOLUTION:

                try:
                    consultation = job.consultation

                    if consultation is not None:
                        consultation.style_evolution_status = "failed"
                        consultation.save(
                            update_fields=["style_evolution_status"]
                        )

                except Exception as status_error:
                    print("Could not update Style Evolution status:")
                    print(
                        type(status_error).__name__,
                        str(status_error),
                    )

        # ======================================================
        # Save final job status
        # ======================================================

        job.save()