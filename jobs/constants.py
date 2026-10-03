# jobs/constants.py

from django.db import models


class JobStatus(models.TextChoices):
    PENDING = "PENDING", "Pending"
    RUNNING = "RUNNING", "Running"
    COMPLETED = "COMPLETED", "Completed"
    FAILED = "FAILED", "Failed"


class JobType(models.TextChoices):
    STYLE_GENERATION = "STYLE_GENERATION", "Style Generation"
    STYLE_EVOLUTION = "STYLE_EVOLUTION", "Style Evolution"
    IMAGE_PROCESSING = "IMAGE_PROCESSING", "Image Processing"