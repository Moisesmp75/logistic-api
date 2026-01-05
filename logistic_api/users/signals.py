from django.db.models.signals import post_save
from django.dispatch import receiver
from ..profile.models import DriverProfile, ClientProfile, InternalClientProfile
import logging

from .models import User

logger = logging.getLogger(__name__)

@receiver(post_save, sender=User)
def create_related_profile(sender, instance: User, created, **kwargs):
    if not created:
        return

    if instance.role == User.Roles.DRIVER:
        DriverProfile.objects.create(user=instance)

    elif instance.role == User.Roles.CLIENT:
        ClientProfile.objects.create(user=instance)

    # elif instance.role == User.Roles.INTERNAL_CLIENT:
    #     InternalClientProfile.objects.create(user=instance)
    #     logger.info(f'CLIENT CREATED: email {instance.email} - id {instance.id}')

