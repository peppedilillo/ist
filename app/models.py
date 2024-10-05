from django.db import models

from django.conf import settings


class Post(models.Model):
    date = models.DateTimeField(auto_now_add=True)
    title = models.CharField(max_length=120)
    url = models.CharField(max_length=300)
    votes = models.IntegerField(default=1)
    user = models.ForeignKey(to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.title} ({self.url})"
