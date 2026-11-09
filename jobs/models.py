from django.db import models

from jobs.constants import JobStatus, JobType
from selfmirror.models import StyleConsultation, PieceStyling


class Job(models.Model):

    job_type = models.CharField(
        max_length=50,
        choices=JobType.choices,
    )

    job_status = models.CharField(
        max_length=20,
        choices=JobStatus.choices,
        default=JobStatus.PENDING,
    )

    # Existing outfit-generation jobs
    consultation = models.ForeignKey(
        StyleConsultation,
        on_delete=models.CASCADE,
        related_name="jobs",
        null=True,
        blank=True,
    )

    # New independent Style My Piece jobs
    piece_styling = models.ForeignKey(
        PieceStyling,
        on_delete=models.CASCADE,
        related_name="jobs",
        null=True,
        blank=True,
    )

    payload = models.JSONField(
        default=dict,
        blank=True,
    )

    created_at = models.DateTimeField(auto_now_add=True)

    started_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    completed_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    error_message = models.TextField(blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        if self.piece_styling_id:
            target = f"Piece Styling {self.piece_styling_id}"
        else:
            target = f"Consultation {self.consultation_id}"

        return f"{self.job_type} | {self.job_status} | {target}"