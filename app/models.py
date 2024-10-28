from django.contrib.auth import get_user_model
from django.db import models
from django.utils import timezone

import pghistory

from .settings import BOARD_PREFIX_SEPARATOR
from .scores import compute_score


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
    user = models.ForeignKey(to=get_user_model(), on_delete=models.CASCADE)
    date = models.DateTimeField()
    board = models.ForeignKey(to=Board, on_delete=models.SET_NULL, related_name="posts", null=True, blank=True)
    keywords = models.ManyToManyField(Keyword, related_name="posts", blank=True)
    fans = models.ManyToManyField(to=get_user_model(), related_name="liked_posts", editable=False)
    score = models.FloatField(editable=False)

    def __str__(self):
        return f"{self.title} ({self.url})"

    def nlikes(self):
        return 1 + self.fans.count()

    def save(self, *args, **kwargs):
        if self.pk is None:
            # object has been just created and has yet to be saved
            self.date = timezone.now()
            self.score = compute_score(1, self.date)
        elif Post.objects.get(pk=self.pk).nlikes() != self.nlikes():
            # number of votes changed
            self.score = compute_score(self.nlikes(), self.date)
        super().save(*args, **kwargs)


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
    user = models.ForeignKey(to=get_user_model(), on_delete=models.CASCADE)
    date = models.DateTimeField(auto_now_add=True)
    post = models.ForeignKey(to=Post, on_delete=models.CASCADE, related_name="comments")
    # parent is null if comment is at top level (a comment to a post)
    parent = models.ForeignKey(to="self", on_delete=models.CASCADE, related_name="replies", null=True)
    fans = models.ManyToManyField(to=get_user_model(), related_name="liked_comments", editable=False)

    def __str__(self):
        return f"Comment by {self.user.username} on {self.post.title}"

    def nlikes(self):
        return 1 + self.fans.count()
