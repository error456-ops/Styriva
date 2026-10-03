from django.db import models

from jobs.constants import JobStatus, JobType
from selfmirror.models import StyleConsultation


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

    consultation = models.ForeignKey(
        StyleConsultation,
        on_delete=models.CASCADE,
        related_name="jobs",
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

    error_message = models.TextField(
        blank=True,
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        
        return (
            
            f"{self.job_type} | {self.job_status} | "
            f"Consultation {self.consultation_id}"
    )