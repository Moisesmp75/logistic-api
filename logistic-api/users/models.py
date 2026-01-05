import uuid
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from .managers import UserManager


class User(AbstractBaseUser, PermissionsMixin):
    class Roles(models.TextChoices):
        ADMIN = 'admin', 'Admin'
        DRIVER = 'driver', 'Driver'
        CLIENT = 'client', 'Client'
        INTERNAL = 'internal', 'Internal'
        INTERNAL_CLIENT = 'internal_client', 'Internal Client'


    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)

    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    role = models.CharField(
        max_length=20,
        choices=Roles.choices,
        default=Roles.CLIENT
    )

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.email