from django.contrib.auth.models import AbstractUser
from django.db import models


class CustomUser(AbstractUser):
    class Status(models.TextChoices):
        ADMIN = "a", "admin"
        MODERATOR = "m", "moderator"
        USER = "u", "user"
        BANNED = "b", "banned"

    status = models.CharField(
        max_length=1,
        choices=Status,
        default=Status.USER,
    )

    def is_admin(self):
        return self.status == self.Status.ADMIN

    def is_mod(self):
        return self.status == self.Status.MODERATOR

    def is_banned(self):
        return self.status == self.Status.BANNED

    def has_mod_rights(self):
        return self.is_mod() or self.is_admin()
