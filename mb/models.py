from django.db import models
from django.db.models import Exists, OuterRef, Prefetch
from astrowebsite.settings import AUTH_USER_MODEL

import pghistory

from .scores import compute_score


CustomUser = AUTH_USER_MODEL


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


class PostManager(models.Manager):
    def with_fan_status(self, user: CustomUser):
        """Returns posts annotated with whether the given user has liked them"""
        # we ask the db to annotate the post with a flag indicating wether the
        # request user has liked the posts we fetched or not. this is because
        # we have to highlight posts liked by the user. the request is at db level
        # to improve performances and avoid n+1 queries.
        return self.annotate(
            is_fan=Exists(
                self.model.fans.through.objects.filter(
                    post_id=OuterRef("id"),
                    customuser_id=user.id,
                )
            )
        )


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
    date = models.DateTimeField(auto_now_add=True)
    edited = models.BooleanField(default=False)
    score = models.FloatField(editable=False, default=0)
    fans = models.ManyToManyField(to=CustomUser, related_name="liked_posts", editable=False)
    keywords = models.ManyToManyField(Keyword, related_name="posts", blank=True)
    board = models.ForeignKey(to=Board, on_delete=models.SET_NULL, related_name="posts", null=True, blank=True)
    user = models.ForeignKey(to=CustomUser, related_name="posts", on_delete=models.CASCADE)
    # to avoid dealing with counts we memorize the number of likes and update it at save time.
    nlikes = models.IntegerField(default=0)
    ncomments = models.IntegerField(default=0)
    pinned = models.BooleanField(default=False)
    objects = PostManager()

    def __str__(self):
        return f"{self.title} ({self.url})"

    def save(self, *args, **kwargs):
        if self.pk is None:
            # object has been just created and has yet to be saved
            super().save(*args, **kwargs)
            # we update the object to have its initial score computed
            self.fans.add(self.user)
            self.nlikes = 1
            self.score = compute_score(self.nlikes, self.date)
            super().save(*args, **kwargs)
        else:
            original_post = Post.objects.get(pk=self.pk)
            if self.title != original_post.title or self.url != original_post.url:
                self.edited = True
            current_fans = self.fans.count()
            if current_fans != original_post.nlikes:
                self.nlikes = current_fans
                self.score = compute_score(self.nlikes, self.date)

            super().save(*args, **kwargs)
        return

    def board_prefix(self):
        return f"{self.board.get_name_display()}" if self.board else ""


class CommentManager(models.Manager):
    def with_fan_status(self, user: CustomUser):
        return self.annotate(
            is_fan=Exists(
                self.model.fans.through.objects.filter(
                    comment_id=OuterRef("id"),
                    customuser_id=user.id,
                )
            )
        )

    def with_nested_replies(self, depth: int, user: CustomUser):
        """Gets comments with nested replies up to specified depth, including fan status"""
        comments = self.with_fan_status(user).select_related("user")
        prefetch_chain = [
            Prefetch(
                "__".join(["replies"] * i),
                queryset=self.with_fan_status(user).select_related("user"),
            )
            for i in range(1, depth + 1)
        ]

        return comments.prefetch_related(*prefetch_chain)


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
    user = models.ForeignKey(to=CustomUser, related_name="comments", on_delete=models.CASCADE)
    date = models.DateTimeField(auto_now_add=True)
    # parent is null if comment is at top level (a comment to a post)
    edited = models.BooleanField(default=False)
    # to avoid dealing with counts we memorize the number of likes and update it at save time.
    nlikes = models.IntegerField(default=0)
    post = models.ForeignKey(to=Post, on_delete=models.CASCADE, related_name="comments")
    parent = models.ForeignKey(to="self", on_delete=models.CASCADE, related_name="replies", null=True)
    fans = models.ManyToManyField(to=CustomUser, related_name="liked_comments", editable=False)
    objects = CommentManager()

    def __str__(self):
        return f"Comment by {self.user.username} on {self.post.title}"

    def save(self, *args, **kwargs):
        if self.pk is None:
            super().save(*args, **kwargs)
            self.fans.add(self.user)
            self.nlikes = 1
            super().save(*args, **kwargs)
            # also post needs updating
            self.post.ncomments += 1
            self.post.save(update_fields=["ncomments"])
        else:
            original_comment = Comment.objects.get(pk=self.pk)
            if self.content != original_comment.content:
                self.edited = True
            current_fans = self.fans.count()
            if current_fans != original_comment.nlikes:
                self.nlikes = current_fans

            super().save(*args, **kwargs)
        return

    def delete(self, *args, **kwargs):
        post = self.post
        super().delete(*args, **kwargs)
        post.ncomments = post.comments.count()
        self.post.save(update_fields=["ncomments"])
