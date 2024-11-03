from functools import partial

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.paginator import Paginator
from django.http import HttpResponse
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect
from django.shortcuts import render
from django.views.decorators.http import require_POST
from django.db.models import Exists, OuterRef, Prefetch, Count

from .forms import CommentForm
from .forms import PostEditForm
from .forms import PostForm
from .models import Board
from .models import Comment
from .models import CommentHistory
from .models import Post
from .settings import INDEX_NPOSTS
from .settings import MAX_DEPTH
from .settings import PROFILE_NENTRIES

EMPTY_MESSAGE = "It is empty here!"


def _index(request, title: str, order_by: str) -> HttpResponse:
    posts = Post.objects.annotate(
        is_fan=Exists(
            Post.fans.through.objects.filter(
                post_id=OuterRef('id'),
                customuser_id=request.user.id,
            )),
        comment_count=Count('comments'),
    ).select_related("user", "board").order_by(order_by)
    paginator = Paginator(posts, INDEX_NPOSTS)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    context = {
        "page_obj": page_obj,
        "header": title,
        "empty_message": EMPTY_MESSAGE,
    }
    return render(request, "mb/index.html", context)


index = partial(_index, title="all", order_by="-score")
news = partial(_index, title="news", order_by="-date")


def _board(request, name: str) -> HttpResponse:
    board = Board.objects.get(name=name)
    # we ask the db to annotate the post with a flag indicating wether the
    # request user has liked the posts we fetched or not. this is because
    # we have to highlight posts liked by the user. the request is at db level
    # to improve performances and avoid n+1 queries.
    posts = Post.objects.annotate(
        is_fan=Exists(
            Post.fans.through.objects.filter(
                post_id=OuterRef('id'),
                customuser_id=request.user.id,
            ),
        comment_count=Count('comments'),
        )).select_related("user", "board").filter(board=board).order_by("-date")
    paginator = Paginator(posts, INDEX_NPOSTS)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    context = {
        "page_obj": page_obj,
        "header": board.get_name_display(),
        "empty_message": EMPTY_MESSAGE,
    }
    return render(request, "mb/index.html", context)


papers = partial(_board, name="p")
code = partial(_board, name="c")
jobs = partial(_board, name="j")


def eager_replies(comments, depth: int, user_id=None):
    base_annotation = Exists(
        Comment.fans.through.objects.filter(
            comment_id=OuterRef('id'),
            customuser_id=user_id,
        )
    )
    # annotate top level comments
    comments = comments.select_related("user").annotate(is_fan=base_annotation)
    # annotate and prefetch nested comments
    prefetch_chain = [
        Prefetch(
            "__".join(["replies"] * i),
            queryset=Comment.objects.select_related('user').annotate(is_fan=base_annotation)
        )
        for i in range(1, depth + 1)
    ]
    return comments.prefetch_related(*prefetch_chain)


def post_detail(request, post_id: int) -> HttpResponse:
    # TODO: this could be achieved with one less db query prefetching comments
    post = get_object_or_404(Post, pk=post_id)
    post.is_fan = post.fans.through.objects.filter(customuser_id=request.user.id).exists()
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


def post_submit(request) -> HttpResponse:
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


def post_edit(request, post_id: int) -> HttpResponse:
    post = get_object_or_404(Post, pk=post_id)
    if not can_edit(request.user, post):
        return redirect(settings.LOGIN_URL)

    if request.method == "POST":
        form = PostEditForm(request.POST, instance=post)
        if form.is_valid():
            post.save()
            return redirect("mb:post_detail", post_id=post.id)
    else:
        form = PostEditForm()
    return render(request, "mb/post_edit.html", {"form": form, "post": post})


def post_delete(request, post_id: int) -> HttpResponse:
    post = get_object_or_404(Post, pk=post_id)
    if not can_edit(request.user, post):
        return redirect(settings.LOGIN_URL)

    if request.method == "GET":
        return render(request, "mb/post_delete.html", {"post": post})
    post.delete()
    return redirect("mb:index")


@require_POST  # allows for embedding under post detail
def post_comment(request, post_id: int) -> HttpResponse:
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


def comment_detail(request, comment_id: int) -> HttpResponse:
    comment = get_object_or_404(
        Comment.objects.select_related('post'),
        pk=comment_id
    )
    comments = eager_replies(
        Comment.objects.filter(pk=comment_id),
        depth=MAX_DEPTH,
        user_id=request.user.id,
    ).order_by("-date")
    context = {
        "post": comment.post,
        "comments": comments,
        "max_depth": MAX_DEPTH,
    }
    return render(request, "mb/post_detail.html", context)


def comment_reply(request, comment_id: int) -> HttpResponse:
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


def comment_delete(request, comment_id: int) -> HttpResponse:
    comment = get_object_or_404(Comment, pk=comment_id)
    if not can_edit(request.user, comment):
        return redirect(settings.LOGIN_URL)

    if request.method == "GET":
        return render(request, "mb/comment_delete.html", {"comment": comment})
    elif request.method == "POST":
        comment.delete()
        return redirect("mb:post_detail", post_id=comment.post.id)
    return redirect("mb:post_detail", post_id=comment.post.id)


def comment_edit(request, comment_id: int) -> HttpResponse:
    comment = get_object_or_404(Comment, pk=comment_id)
    if not can_edit(request.user, comment):
        return redirect(settings.LOGIN_URL)

    if request.method == "POST":
        form = CommentForm(request.POST, instance=comment)
        if form.is_valid():
            comment.save()
            return redirect("mb:post_detail", post_id=comment.post.id)
    else:
        form = CommentForm()
    return render(request, "mb/comment_edit.html", {"form": form, "comment": comment})


def comment_history(request, comment_id: int) -> HttpResponse:
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


def can_upvote(user):
    return user.is_authenticated and not user.is_banned()


@require_POST
def _upvote(
    request,
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
    return JsonResponse({"success": True, "nlikes": item.fans.count(), "isupvote": isupvote})


def comment_upvote(request, comment_id: int):
    return _upvote(request, comment_id, Comment)


def post_upvote(request, post_id: int):
    return _upvote(request, post_id, Post)


def profile(request, user_id: int):
    user = get_object_or_404(get_user_model(), pk=user_id)
    posts = user.posts.select_related("user")
    comments = user.comments.select_related("user")

    paginator = Paginator(
        [
            {"content": c, "ispost": isinstance(c, Post)}
            for c in sorted((*posts, *comments), key=lambda x: x.date, reverse=True)
        ],
        PROFILE_NENTRIES,
    )
    context = {
        "user": user,
        "page_obj": paginator.get_page(request.GET.get("page")),
        "empty_message": EMPTY_MESSAGE,
    }
    return render(request, "accounts/profile.html", context)
