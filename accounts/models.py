from django.conf import settings
from django.db import models


class Profile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile",
    )

    # Purchased credits
    credits = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.user.username


class UserUsage(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="usage",
    )

    # Free guest experience
    guest_free_used = models.BooleanField(default=False)

    # Free experience after signup
    signup_free_used = models.BooleanField(default=False)

    # Analytics
    total_generations = models.PositiveIntegerField(default=0)
    total_style_evolutions = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def has_free_generation(self):
        return (
            not self.guest_free_used
            or not self.signup_free_used
        )

    def __str__(self):
        return f"{self.user.username} Usage"
        
        

    
    
class Payment(models.Model):

    STATUS_CHOICES = [
        ("created", "Created"),
        ("paid", "Paid"),
        ("failed", "Failed"),
    ]

    PLAN_CHOICES = [
        ("starter", "Starter"),
        ("premium", "Premium"),
        ("creator", "Creator"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="payments",
    )

    plan = models.CharField(
        max_length=20,
        choices=PLAN_CHOICES,
    )

    amount = models.PositiveIntegerField()
    credits = models.PositiveIntegerField()

    razorpay_order_id = models.CharField(
        max_length=100,
        unique=True,
    )

    razorpay_payment_id = models.CharField(
        max_length=100,
        unique=True,
        null=True,
        blank=True,
    )

    razorpay_signature = models.CharField(
        max_length=255,
        blank=True,
        default="",
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="created",
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    paid_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    def __str__(self):
        return (
            f"{self.user.username} - "
            f"{self.plan} - "
            f"₹{self.amount / 100:.2f} - "
            f"{self.status}"
        )