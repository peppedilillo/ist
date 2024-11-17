from functools import partial

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.paginator import Paginator
from django.http import HttpResponse, HttpRequest
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect
from django.shortcuts import render
from django.views.decorators.http import require_POST
from django.db.models import Count

from .forms import CommentForm
from .forms import PostEditForm
from .forms import PostForm
from .models import Comment
from .models import CommentHistory
from .models import Post
from .settings import INDEX_NPOSTS
from .settings import MAX_DEPTH

EMPTY_MESSAGE = "It is empty here!"


CustomUser = get_user_model()


def _index(
    request: HttpRequest,
    order_by: str,
    filter: dict,
    header: str | None = None,
) -> HttpResponse:
    # fmt: off
    posts = (
        Post.objects
        .with_fan_status(request.user)
        .select_related("user", "board")
        .order_by("-pinned", order_by)
        .filter(**filter)
    )
    # fmt: on
    # TODO: fix this paginator so we can have one queries for the homepage
    paginator = Paginator(posts, INDEX_NPOSTS)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    context = {"page_obj": page_obj, "empty_message": EMPTY_MESSAGE}
    if header:
        context["header"] = header
    return render(request, "mboard/index.html", context)


index = partial(
    _index,
    header="all",
    filter={},
    order_by="-score",
)
news = partial(
    _index,
    header="news",
    filter={},
    order_by="-date",
)
papers = partial(
    _index,
    header="papers",
    filter={"board__name": "p"},
    order_by="-score",
)
code = partial(
    _index,
    header="code",
    filter={"board__name": "c"},
    order_by="-score",
)
jobs = partial(
    _index,
    header="jobs",
    filter={"board__name": "j"},
    order_by="-score",
)


def post_detail(request: HttpRequest, post_id: int) -> HttpResponse:
    post = get_object_or_404(Post.objects.with_fan_status(request.user), pk=post_id)
    # fmt: off
    comments = (
        Comment.objects
        .with_nested_replies(MAX_DEPTH, request.user)
        .filter(parent=None, post=post)
        .order_by("-date")
    )
    # fmt: on
    comment_form = CommentForm()
    return render(
        request,
        "mboard/post_detail.html",
        {
            "post": post,
            "comments": comments,
            "comment_form": comment_form,
            "max_depth": MAX_DEPTH,
        },
    )


def can_submit(user: CustomUser):
    return user.is_authenticated and not user.is_banned()


def can_edit(user: CustomUser, contrib: Post | Comment):
    return user.is_authenticated and not user.is_banned() and (user == contrib.user or user.has_mod_rights())


def post_submit(request: HttpRequest) -> HttpResponse:
    if not can_submit(request.user):
        return redirect(settings.LOGIN_URL)

    if request.method == "POST":
        form = PostForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.user = request.user
            post.save()
            return redirect("mboard:index")
    else:
        form = PostForm()
    return render(
        request,
        "mboard/post_submit.html",
        {
            "form": form,
        },
    )


def post_edit(request: HttpRequest, post_id: int) -> HttpResponse:
    post = get_object_or_404(Post.objects.with_fan_status(request.user), pk=post_id)
    if not can_edit(request.user, post):
        return redirect(settings.LOGIN_URL)

    if request.method == "POST":
        form = PostEditForm(request.POST, instance=post)
        if form.is_valid():
            post.save()
            return redirect("mboard:post_detail", post_id=post.id)
    else:
        form = PostEditForm(instance=post)
    return render(
        request,
        "mboard/post_edit.html",
        {
            "form": form,
            "post": post,
        },
    )


def post_delete(request: HttpRequest, post_id: int) -> HttpResponse:
    post = get_object_or_404(Post, pk=post_id)
    if not can_edit(request.user, post):
        return redirect(settings.LOGIN_URL)

    if request.method == "GET":
        return render(
            request,
            "mboard/post_delete.html",
            {
                "post": post,
            },
        )
    post.delete()
    return redirect("mboard:index")


@require_POST  # allows for embedding under post detail
def post_comment(request: HttpRequest, post_id: int) -> HttpResponse:
    """Adds a top level comment to a post."""
    if not can_submit(request.user):
        return redirect(settings.LOGIN_URL)

    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.post = post
        comment.user = request.user
        comment.parent = None
        comment.save()
    return redirect("mboard:post_detail", post_id=post_id)


def can_pin(user: CustomUser):
    return user.has_mod_rights()


def post_pin(request: HttpRequest, post_id: int) -> HttpResponse:
    if not can_pin(request.user):
        return redirect(settings.LOGIN_URL)

    post = get_object_or_404(Post, pk=post_id)
    if request.method == "GET":
        return render(request, "mboard/post_pin.html", {"post": post})
    post.pinned = not post.pinned
    post.save()
    return redirect("mboard:index")


def comment_detail(request: HttpRequest, comment_id: int) -> HttpResponse:
    comment = get_object_or_404(Comment.objects.select_related("post"), pk=comment_id)
    # fmt: off
    comments = (
        Comment.objects
        .with_nested_replies(MAX_DEPTH, request.user)
        .filter(pk=comment_id)
        .order_by("-date")
    )
    # fmt: on
    post = Post.objects.with_fan_status(request.user).get(pk=comment.post.pk)
    return render(
        request,
        "mboard/post_detail.html",
        {
            "post": post,
            "comments": comments,
            "max_depth": MAX_DEPTH,
        },
    )


def comment_reply(request: HttpRequest, comment_id: int) -> HttpResponse:
    if not can_submit(request.user):
        return redirect(settings.LOGIN_URL)

    comment = get_object_or_404(Comment, pk=comment_id)
    if request.method == "POST":
        form = CommentForm(request.POST)
        if form.is_valid():
            reply = form.save(commit=False)
            reply.post = comment.post
            reply.user = request.user
            reply.parent = comment
            reply.save()
            return redirect("mboard:post_detail", post_id=reply.post.id)
    else:
        form = CommentForm()
    return render(
        request,
        "mboard/comment_reply.html",
        {
            "form": form,
            "comment": comment,
        },
    )


def comment_delete(request: HttpRequest, comment_id: int) -> HttpResponse:
    comment = get_object_or_404(Comment, pk=comment_id)
    if not can_edit(request.user, comment):
        return redirect(settings.LOGIN_URL)

    if request.method == "GET":
        return render(request, "mboard/comment_delete.html", {"comment": comment})
    elif request.method == "POST":
        comment.delete()
        return redirect("mboard:post_detail", post_id=comment.post.id)
    return redirect("mboard:post_detail", post_id=comment.post.id)


def comment_edit(request: HttpRequest, comment_id: int) -> HttpResponse:
    comment = get_object_or_404(Comment, pk=comment_id)
    if not can_edit(request.user, comment):
        return redirect(settings.LOGIN_URL)

    if request.method == "POST":
        form = CommentForm(request.POST, instance=comment)
        if form.is_valid():
            comment.save()
            return redirect("mboard:post_detail", post_id=comment.post.id)
    else:
        form = CommentForm(instance=comment)
    return render(
        request,
        "mboard/comment_edit.html",
        {
            "form": form,
            "comment": comment,
        },
    )


def comment_history(request: HttpRequest, comment_id: int) -> HttpResponse:
    comment = get_object_or_404(Comment, pk=comment_id)
    history = [
        {
            "content": c["content"],
            "date": c["pgh_created_at"],
        }
        for c in CommentHistory.objects.filter(pgh_obj=comment).values()
    ]
    context = {"history": history, "comment": comment}
    return render(
        request,
        "mboard/comment_history.html",
        {
            "history": history,
            "comment": comment,
        },
    )


def can_upvote(user) -> bool:
    return user.is_authenticated and not user.is_banned()


@require_POST
def _upvote(
    request: HttpRequest,
    contrib_id: int,
    contrib_model: Post | Comment,
):
    if not can_upvote(request.user):
        return JsonResponse({"success": False})

    item = get_object_or_404(contrib_model, pk=contrib_id)
    if item.fans.contains(request.user):
        item.fans.remove(request.user)
        isupvote = False
    else:
        item.fans.add(request.user)
        isupvote = True
    item.save()
    return JsonResponse(
        {
            "success": True,
            "nlikes": item.nlikes,
            "isupvote": isupvote,
        }
    )


def comment_upvote(request: HttpRequest, comment_id: int):
    return _upvote(request, comment_id, Comment)


def post_upvote(request: HttpRequest, post_id: int):
    return _upvote(request, post_id, Post)


def profile(request: HttpRequest, user_id: int) -> HttpResponse:
    user = get_object_or_404(
        get_user_model().objects.annotate(
            post_count=Count("posts", distinct=True),
            comment_count=Count("comments", distinct=True),
        ),
        pk=user_id,
    )
    return render(
        request,
        "mboard/profile.html",
        {
            "user": user,
        },
    )


def profile_posts(request: HttpRequest, user_id: int) -> HttpResponse:
    _ = get_object_or_404(get_user_model(), pk=user_id)
    return _index(request, post_objects=Post.objects.filter(user_id=user_id), order_by="-date")


def profile_comments(request: HttpRequest, user_id: int) -> HttpResponse:
    _ = get_object_or_404(get_user_model(), pk=user_id)
    # fmt: off
    comments = (
        Comment.objects
        .with_nested_replies(MAX_DEPTH, request.user)
        .filter(user_id=user_id)
        .order_by("-date")
    )
    # fmt: on
    return render(
        request,
        "mboard/post_detail.html",
        {
            "comments": comments,
            "max_depth": MAX_DEPTH,
        },
    )
