from django.db import models
from django.conf import settings


class StyleConsultation(models.Model):

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="style_consultations",
        null=True,
        blank=True,
    )

    gender = models.CharField(
        max_length=10,
        choices=[
            ("women", "Women"),
            ("men", "Men"),
        ],
        default="women",
    )

    occasion = models.CharField(max_length=100)
    vibe = models.CharField(max_length=100)
    weather = models.CharField(max_length=100)

    # ==========================================================
    # User Reference Photo
    # ==========================================================

    user_model_photo = models.ImageField(
        upload_to="user_model_photos/"
    )

    # ==========================================================
    # Tops
    # ==========================================================

    top_1 = models.ImageField(upload_to="tops/")
    top_2 = models.ImageField(upload_to="tops/")
    top_3 = models.ImageField(upload_to="tops/")

    # ==========================================================
    # Bottoms
    # ==========================================================

    bottom_1 = models.ImageField(upload_to="bottoms/")
    bottom_2 = models.ImageField(upload_to="bottoms/")
    bottom_3 = models.ImageField(upload_to="bottoms/")

    # ==========================================================
    # Shoes (NEW, optional)
    # ==========================================================

    shoe_1 = models.ImageField(upload_to="shoes/", blank=True, null=True)
    shoe_2 = models.ImageField(upload_to="shoes/", blank=True, null=True)
    shoe_3 = models.ImageField(upload_to="shoes/", blank=True, null=True)

    # ==========================================================
    # Scarves
    # ==========================================================

    scarf_1 = models.ImageField(upload_to="scarves/", blank=True, null=True)
    scarf_2 = models.ImageField(upload_to="scarves/", blank=True, null=True)
    scarf_3 = models.ImageField(upload_to="scarves/", blank=True, null=True)

    # ==========================================================
    # Style Evolution Status
    # ==========================================================

    style_evolution_status = models.CharField(
        max_length=20,
        default="pending",
        choices=[
            ("pending", "Pending"),
            ("processing", "Processing"),
            ("completed", "Completed"),
            ("failed", "Failed"),
        ],
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return (
            f"{self.occasion} | "
            f"{self.vibe} | "
            f"{self.weather}"
        )


# ==============================================================
# Generated Look
# ==============================================================

class GeneratedLook(models.Model):

    consultation = models.ForeignKey(
        StyleConsultation,
        on_delete=models.CASCADE,
        related_name="generated_looks"
    )

    # AI Selected Outfit

    selected_top = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )

    selected_bottom = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )

    selected_shoe = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )

    selected_scarf = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )

    # AI Score

    look_number = models.PositiveIntegerField(
        default=1
    )

    score = models.FloatField(
        default=0
    )

    title = models.CharField(
        max_length=255
    )

    # AI Explanation

    styling_rationale = models.TextField(
        blank=True,
        null=True
    )

    makeup_recommendation = models.TextField(
        blank=True,
        null=True
    )

    hair_recommendation = models.TextField(
        blank=True,
        null=True
    )

    accessory_recommendation = models.TextField(
        blank=True,
        null=True
    )

    render_prompt = models.TextField(
        blank=True,
        null=True
    )

    generated_image = models.ImageField(
        upload_to="generated_looks/",
        blank=True,
        null=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return (
            f"Look {self.look_number} - "
            f"{self.title}"
        )


# ==============================================================
# Style Evolution
# ==============================================================

class EvolvedLook(models.Model):

    generated_look = models.ForeignKey(
        GeneratedLook,
        on_delete=models.CASCADE,
        related_name="evolved_looks"
    )

    evolved_image = models.ImageField(
        upload_to="evolved_looks/"
    )

    style_preference = models.CharField(
        max_length=50,
        choices=[
            ("minimal", "Minimal Luxury"),
            ("elegant", "Elegant Evening"),
            ("statement", "Statement Fashion"),
        ]
    )

    selected_extras = models.JSONField(
        default=list,
        blank=True
    )

    added_items = models.JSONField(
        default=list,
        blank=True
    )

    reasoning = models.TextField()

    makeup_recommendation = models.TextField(
        blank=True,
        default=""
    )

    hair_recommendation = models.TextField(
        blank=True,
        default=""
    )

    accessory_recommendation = models.TextField(
        blank=True,
        default=""
    )

    render_prompt = models.TextField(
        blank=True,
        default=""
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return (
            f"Evolution - "
            f"{self.generated_look.title} "
            f"({self.style_preference})"
        )