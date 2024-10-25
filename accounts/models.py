from django.apps import apps
from django.contrib.auth.models import AbstractUser
from django.db import models


class CustomUser(AbstractUser):
    class Status(models.TextChoices):
        ADMIN = "a", "admin"
        MODERATOR = "m", "moderator"
        USER = "u", "user"
        BANNED = "b", "banned"

    karma = models.IntegerField(default=1)
    status = models.CharField(
        max_length=1,
        choices=Status,
        default=Status.USER,
    )

    def contributions(self):
        posts = apps.get_model("app", "Post").objects.filter(user=self)
        comments = apps.get_model("app", "Comment").objects.filter(user=self)
        return sorted((*posts, *comments), key=lambda x: x.date, reverse=True)

    def is_admin(self):
        return self.status == self.Status.ADMIN

    def is_mod(self):
        return self.status == self.Status.MODERATOR

    def is_banned(self):
        return self.status == self.Status.BANNED

    def has_mod_rights(self):
        return self.is_mod() or self.is_admin()
