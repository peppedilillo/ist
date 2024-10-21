from django.contrib.auth import get_user_model
from django.db import models

from .settings import BOARD_PREFIX_SEPARATOR


class Board(models.Model):
    name = models.CharField(max_length=10)

    def __str__(self):
        return self.name

    def prefix(self):
        return f"{self.name}{BOARD_PREFIX_SEPARATOR} " if self.prefix else ""


class Keyword(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name


class Post(models.Model):
    title = models.CharField(max_length=120)
    url = models.CharField(max_length=300)
    votes = models.IntegerField(default=1)
    user = models.ForeignKey(to=get_user_model(), on_delete=models.CASCADE)
    date = models.DateTimeField(auto_now_add=True)
    board = models.ForeignKey(to=Board, on_delete=models.SET_NULL, related_name="posts", null=True, blank=True)
    keywords = models.ManyToManyField(Keyword, related_name="posts", blank=True)

    def __str__(self):
        return f"{self.title} ({self.url})"


class Comment(models.Model):
    content = models.TextField(max_length=10_000)
    votes = models.IntegerField(default=1)
    # related_name enable calling like `post.comments.order_by("..")
    post = models.ForeignKey(to=Post, on_delete=models.CASCADE, related_name="comments")
    # parent is null if comment is at top level (a comment to a post)
    parent = models.ForeignKey(to="self", on_delete=models.CASCADE, related_name="replies", null=True)
    user = models.ForeignKey(to=get_user_model(), on_delete=models.CASCADE)
    date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Comment by {self.user.username} on {self.post.title}"
