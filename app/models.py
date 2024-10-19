from django.contrib.auth import get_user_model
from django.db import models

from .settings import BOARDS, BOARDS_PREFIXES, BOARD_PREFIX_SEPARATOR


class Post(models.Model):
    title = models.CharField(max_length=120)
    url = models.CharField(max_length=300)
    votes = models.IntegerField(default=1)
    user = models.ForeignKey(to=get_user_model(), on_delete=models.CASCADE)
    date = models.DateTimeField(auto_now_add=True)
    board = models.CharField(
        max_length=max(map(len, BOARDS.keys())),
        choices=BOARDS,
        null=True,
    )

    def __str__(self):
        return f"{self.title} ({self.url})"

    def prefix(self):
        if self.board is not None:
            return f"{BOARDS_PREFIXES[self.board]}{BOARD_PREFIX_SEPARATOR} "
        return ""


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
