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
from django.db.models import Exists, OuterRef, Prefetch, Count
from django.db.models.query import QuerySet

from .forms import CommentForm
from .forms import PostEditForm
from .forms import PostForm
from .models import Board
from .models import Comment
from .models import CommentHistory
from .models import Post
from .settings import INDEX_NPOSTS
from .settings import MAX_DEPTH

EMPTY_MESSAGE = "It is empty here!"


def _index(
    request: HttpRequest,
    post_objects: QuerySet,
    order_by: str,
    header: str | None = None,
) -> HttpResponse:
    # we ask the db to annotate the post with a flag indicating wether the
    # request user has liked the posts we fetched or not. this is because
    # we have to highlight posts liked by the user. the request is at db level
    # to improve performances and avoid n+1 queries.
    posts = (
        post_objects.annotate(
            is_fan=Exists(
                Post.fans.through.objects.filter(
                    post_id=OuterRef("id"),
                    customuser_id=request.user.id,
                )
            ),
        )
        .select_related("user", "board")
        .order_by("-pinned", order_by)
    )
    # TODO: fix this paginator so we can have one queries for the homepage
    paginator = Paginator(posts, INDEX_NPOSTS)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    context = {"page_obj": page_obj, "empty_message": EMPTY_MESSAGE}
    if header:
        context["header"] = header
    return render(request, "mb/index.html", context)


index = partial(
    _index,
    header="all",
    post_objects=Post.objects.all(),
    order_by="-score",
)
news = partial(
    _index,
    header="news",
    post_objects=Post.objects.all(),
    order_by="-date",
)
papers = partial(
    _index,
    header="papers",
    post_objects=Post.objects.filter(board__name="p"),
    order_by="-score",
)
code = partial(
    _index,
    header="code",
    post_objects=Post.objects.filter(board__name="c"),
    order_by="-score",
)
jobs = partial(
    _index,
    header="jobs",
    post_objects=Post.objects.filter(board__name="j"),
    order_by="-score",
)


def eager_replies(comments: QuerySet, depth: int, user_id=None) -> QuerySet:
    base_annotation = Exists(
        Comment.fans.through.objects.filter(
            comment_id=OuterRef("id"),
            customuser_id=user_id,
        )
    )
    # annotate top level comments
    comments = comments.select_related("user").annotate(is_fan=base_annotation)
    # annotate and prefetch nested comments
    prefetch_chain = [
        Prefetch(
            "__".join(["replies"] * i),
            queryset=Comment.objects.select_related("user").annotate(is_fan=base_annotation),
        )
        for i in range(1, depth + 1)
    ]
    return comments.prefetch_related(*prefetch_chain)


def post_detail(request: HttpRequest, post_id: int) -> HttpResponse:
    # TODO: this could be achieved with one less db query prefetching comments
    post = get_object_or_404(Post, pk=post_id)
    post.is_fan = post.fans.filter(id=request.user.id).exists()
    comments = eager_replies(
        post.comments.filter(parent=None),
        depth=MAX_DEPTH,
        user_id=request.user.id,
    ).order_by("-date")
    comment_form = CommentForm()
    context = {
        "post": post,
        "comments": comments,
        "comment_form": comment_form,
        "max_depth": MAX_DEPTH,
    }
    return render(request, "mb/post_detail.html", context)


def can_submit(user):
    return user.is_authenticated and not user.is_banned()


def can_edit(user, contrib: Post | Comment):
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
            return redirect("mb:index")
    else:
        form = PostForm()
    return render(request, "mb/post_submit.html", {"form": form})


def post_edit(request: HttpRequest, post_id: int) -> HttpResponse:
    post = get_object_or_404(Post, pk=post_id)
    if not can_edit(request.user, post):
        return redirect(settings.LOGIN_URL)

    if request.method == "POST":
        form = PostEditForm(request.POST, instance=post)
        if form.is_valid():
            post.save()
            return redirect("mb:post_detail", post_id=post.id)
    else:
        post.is_fan = post.fans.filter(id=request.user.id).exists()
        form = PostEditForm(instance=post)
    return render(request, "mb/post_edit.html", {"form": form, "post": post})


def post_delete(request: HttpRequest, post_id: int) -> HttpResponse:
    post = get_object_or_404(Post, pk=post_id)
    if not can_edit(request.user, post):
        return redirect(settings.LOGIN_URL)

    if request.method == "GET":
        return render(request, "mb/post_delete.html", {"post": post})
    post.delete()
    return redirect("mb:index")


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
    return redirect("mb:post_detail", post_id=post_id)


def can_pin(user):
    return user.has_mod_rights()


@require_POST
def post_pin(request: HttpRequest, post_id: int) -> HttpResponse:
    if not can_pin(request.user):
        return redirect(settings.LOGIN_URL)

    post = get_object_or_404(Post, pk=post_id)
    post.pinned = not post.pinned
    post.save()
    return redirect("mb:post_detail", post_id=post_id)


def comment_detail(request: HttpRequest, comment_id: int) -> HttpResponse:
    comment = get_object_or_404(Comment.objects.select_related("post"), pk=comment_id)
    comments = eager_replies(
        Comment.objects.filter(pk=comment_id),
        depth=MAX_DEPTH,
        user_id=request.user.id,
    ).order_by("-date")
    comment.post.is_fan = comment.post.fans.filter(id=request.user.id).exists()
    context = {
        "post": comment.post,
        "comments": comments,
        "max_depth": MAX_DEPTH,
    }
    return render(request, "mb/post_detail.html", context)


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
            return redirect("mb:post_detail", post_id=reply.post.id)
    else:
        form = CommentForm()
    return render(request, "mb/comment_reply.html", {"form": form, "comment": comment})


def comment_delete(request: HttpRequest, comment_id: int) -> HttpResponse:
    comment = get_object_or_404(Comment, pk=comment_id)
    if not can_edit(request.user, comment):
        return redirect(settings.LOGIN_URL)

    if request.method == "GET":
        return render(request, "mb/comment_delete.html", {"comment": comment})
    elif request.method == "POST":
        comment.delete()
        return redirect("mb:post_detail", post_id=comment.post.id)
    return redirect("mb:post_detail", post_id=comment.post.id)


def comment_edit(request: HttpRequest, comment_id: int) -> HttpResponse:
    comment = get_object_or_404(Comment, pk=comment_id)
    if not can_edit(request.user, comment):
        return redirect(settings.LOGIN_URL)

    if request.method == "POST":
        form = CommentForm(request.POST, instance=comment)
        if form.is_valid():
            comment.save()
            return redirect("mb:post_detail", post_id=comment.post.id)
    else:
        form = CommentForm(instance=comment)
    return render(request, "mb/comment_edit.html", {"form": form, "comment": comment})


def comment_history(request: HttpRequest, comment_id: int) -> HttpResponse:
    comment = get_object_or_404(Comment, pk=comment_id)
    history = [
        {"content": c["content"], "date": c["pgh_created_at"]}
        for c in CommentHistory.objects.filter(pgh_obj=comment).values()
    ]
    context = {
        "history": history,
        "comment": comment,
    }
    return render(request, "mb/comment_history.html", context)


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
    return render(request, "mb/profile.html", {"user": user})


def profile_posts(request: HttpRequest, user_id: int) -> HttpResponse:
    _ = get_object_or_404(get_user_model(), pk=user_id)
    return _index(request, post_objects=Post.objects.filter(user_id=user_id), order_by="-date")


def profile_comments(request: HttpRequest, user_id: int) -> HttpResponse:
    _ = get_object_or_404(get_user_model(), pk=user_id)
    comments = eager_replies(
        Comment.objects.filter(user_id=user_id),
        depth=MAX_DEPTH,
        user_id=request.user.id,
    ).order_by("-date")
    context = {
        "comments": comments,
        "max_depth": MAX_DEPTH,
    }
    return render(request, "mb/post_detail.html", context)
