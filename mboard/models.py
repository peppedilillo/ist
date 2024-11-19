from django.db import models
from django.db.models import Exists, OuterRef, Prefetch
from ist.settings import AUTH_USER_MODEL

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

    def board_prefix(self):
        return f"{self.board.get_name_display()}" if self.board else ""


def save_new_post(title: str, author: CustomUser, url: str) -> Post:
    post = Post(title=title, user=author, url=url)
    post.save()
    post.fans.add(author)
    post.nlikes = 1
    post.score = compute_score(post.nlikes, post.date)
    post.save(update_fields=["nlikes", "score"])
    return post


def save_edited_post(new_title: str, post: Post) -> Post:
    original_post = Post.objects.get(pk=post.pk)
    if new_title != original_post.title:
        post.edited = True
        post.title = new_title
        post.save(update_fields=["title", "edited"])
    return post


def save_toggle_pin(post: Post):
    post.pinned = not post.pinned
    post.save()
    return post


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

    def delete(self, *args, **kwargs):
        post = self.post
        super().delete(*args, **kwargs)
        post.ncomments = post.comments.count()
        self.post.save(update_fields=["ncomments"])


def save_new_comment(content: str, author: CustomUser, post: Post, parent: Comment | None):
    comment = Comment(content=content, user=author, post=post, parent=parent)
    comment.save()
    comment.fans.add(author)
    comment.nlikes = 1
    comment.save(update_fields=["nlikes"])
    post.ncomments += 1
    post.save(update_fields=["ncomments"])
    return comment


def save_edited_comment(new_content: str, comment: Comment) -> Comment:
    original_comment = Comment.objects.get(pk=comment.pk)
    if new_content != original_comment.content:
        comment.edited = True
        comment.content = new_content
        comment.save(update_fields=["content", "edited"])
    return comment


def save_new_like(content: Comment | Post, fan: CustomUser) -> Comment | Post:
    content.fans.add(fan)
    content.nlikes += 1
    content.save(update_fields=["nlikes"])
    return content


def save_remove_like(content: Comment | Post, fan: CustomUser) -> Comment:
    content.fans.remove(fan)
    content.nlikes -= 1
    content.save(update_fields=["nlikes"])
    return content
