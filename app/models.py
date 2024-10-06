from django.db import models

from django.conf import settings


class Post(models.Model):
    title = models.CharField(max_length=120)
    url = models.CharField(max_length=300)
    votes = models.IntegerField(default=1)
    user = models.ForeignKey(to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} ({self.url})"


class Comment(models.Model):
    # related_name enable calling like `post.comments.order_by("..")
    post = models.ForeignKey(to=Post, on_delete=models.CASCADE, related_name="comments")
    user = models.ForeignKey(to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Comment by {self.user.username} on {self.post.title}'
