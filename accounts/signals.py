from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Profile, UserUsage


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_user_related_models(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)
        UserUsage.objects.create(user=instance)