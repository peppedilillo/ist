from django.contrib.auth import get_user_model
from django.db import models
from django.db.models.constraints import UniqueConstraint
import pghistory

from .settings import BOARD_PREFIX_SEPARATOR


class Board(models.Model):
    class Boards(models.TextChoices):
        PAPERS = "p", "papers"
        CODE = "c", "code"
        JOBS = "j", "jobs"

    name = models.CharField(
        max_length=1,
        choices=Boards,
        null=True,
        unique=True,
        default=None,
    )

    def __str__(self):
        return self.get_name_display()

    def prefix(self):
        return f"{self.get_name_display()}{BOARD_PREFIX_SEPARATOR} " if self.prefix else ""


class Keyword(models.Model):
    class Keywords(models.TextChoices):
        COSMOLOGY = "c", "cosmology"
        EARTH_AND_PLANETS = "p", "earth and planets"
        GALAXIES = "g", "galaxies"
        HIGH_ENERGY = "h", "high energy"
        TECH_AND_METHODS = "t", "tech and methods"
        SUN_AND_STARS = "s", "sun and stars"
        MULTIMESSENGER = "m", "multimessenger"

    name = models.CharField(
        max_length=2,
        choices=Keywords,
        null=True,
        unique=True,
        default=None,
    )

    def __str__(self):
        return self.get_name_display()


@pghistory.track(
    pghistory.UpdateEvent(
        "title_changed",
        row=pghistory.Old,
        condition=pghistory.AnyChange("title"),
    ),
    model_name="PostHistory",
)
class Post(models.Model):
    title = models.CharField(max_length=120)
    url = models.CharField(max_length=300)
    # nvotes is set to a default of 1 but we do not register this vote
    nvotes = models.IntegerField(default=1)
    user = models.ForeignKey(to=get_user_model(), on_delete=models.CASCADE)
    date = models.DateTimeField(auto_now_add=True)
    board = models.ForeignKey(to=Board, on_delete=models.SET_NULL, related_name="posts", null=True, blank=True)
    keywords = models.ManyToManyField(Keyword, related_name="posts", blank=True)

    def __str__(self):
        return f"{self.title} ({self.url})"


@pghistory.track(
    pghistory.UpdateEvent(
        "content_changed",
        row=pghistory.Old,
        condition=pghistory.AnyChange("content"),
    ),
    model_name="CommentHistory",
)
class Comment(models.Model):
    content = models.TextField(max_length=10_000)
    # nvotes is set to a default of 1 but we do not register this vote
    nvotes = models.IntegerField(default=1)
    post = models.ForeignKey(to=Post, on_delete=models.CASCADE, related_name="comments")
    # parent is null if comment is at top level (a comment to a post)
    parent = models.ForeignKey(to="self", on_delete=models.CASCADE, related_name="replies", null=True)
    user = models.ForeignKey(to=get_user_model(), on_delete=models.CASCADE)
    date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Comment by {self.user.username} on {self.post.title}"


class VotePost(models.Model):
    user = models.ForeignKey(to=get_user_model(), on_delete=models.CASCADE)
    date = models.DateTimeField(auto_now_add=True)
    address = models.ForeignKey(to=Post, related_name="votes", on_delete=models.CASCADE)

    # this will enforce an IntegrityError if we try to save more votes
    # from the same user to the same contribution
    class Meta:
        constraints = [UniqueConstraint(fields=('user', 'address'), name="unique_post_vote")]


class VoteComment(models.Model):
    user = models.ForeignKey(to=get_user_model(), on_delete=models.CASCADE)
    date = models.DateTimeField(auto_now_add=True)
    address = models.ForeignKey(to=Comment, related_name="votes", on_delete=models.CASCADE)

    # this will enforce an IntegrityError if we try to save more votes
    # from the same user to the same contribution
    class Meta:
        constraints = [UniqueConstraint(fields=('user', 'address'), name="unique_comment_vote")]
