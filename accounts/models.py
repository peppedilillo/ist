from django.apps import apps
from django.contrib.auth.models import AbstractUser
from django.db import models


class CustomUser(AbstractUser):
    karma = models.IntegerField(default=1)

    def contributions(self):
        posts = apps.get_model("app", "Post").objects.filter(user=self)
        comments = apps.get_model("app", "Comment").objects.filter(user=self)
        return sorted((*posts, *comments), key=lambda x: x.date, reverse=True)
