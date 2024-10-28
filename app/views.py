from functools import partial

from django.conf import settings
from django.core.paginator import Paginator
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect
from django.shortcuts import render
from django.views.decorators.http import require_POST
from django.http import JsonResponse

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


def index(request) -> HttpResponse:
    posts = Post.objects.order_by("-date").all()
    paginator = Paginator(posts, INDEX_NPOSTS)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    context = {
        "page_obj": page_obj,
        "header": "news",
        "show_prefix": True,
        "empty_message": EMPTY_MESSAGE,
    }
    return render(request, "app/index.html", context)


def _board(request, name: str) -> HttpResponse:
    board = Board.objects.get(name=name)
    posts = Post.objects.order_by("-date").filter(board=board)
    paginator = Paginator(posts, INDEX_NPOSTS)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    context = {
        "page_obj": page_obj,
        "header": board.get_name_display(),
        "empty_message": EMPTY_MESSAGE,
    }
    return render(request, "app/index.html", context)


papers = partial(_board, name="p")
code = partial(_board, name="c")
jobs = partial(_board, name="j")


def post_detail(request, post_id: int) -> HttpResponse:
    post = get_object_or_404(Post, pk=post_id)
    comments = post.comments.filter(parent=None).order_by("-date")
    comment_form = CommentForm()
    context = {
        "post": post,
        "comments": comments,
        "show_prefix": True,
        "comment_form": comment_form,
        "max_depth": MAX_DEPTH,
    }
    return render(request, "app/post_detail.html", context)


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
            return redirect("app:index")
    else:
        form = PostForm()
    return render(request, "app/post_submit.html", {"form": form})


def post_edit(request, post_id: int) -> HttpResponse:
    post = get_object_or_404(Post, pk=post_id)
    if not can_edit(request.user, post):
        return redirect(settings.LOGIN_URL)

    if request.method == "POST":
        form = PostEditForm(request.POST, instance=post)
        if form.is_valid():
            post.save()
            return redirect("app:post_detail", post_id=post.id)
    else:
        form = PostEditForm()
    return render(request, "app/post_edit.html", {"form": form, "post": post})


def post_delete(request, post_id: int) -> HttpResponse:
    post = get_object_or_404(Post, pk=post_id)
    if not can_edit(request.user, post):
        return redirect(settings.LOGIN_URL)

    if request.method == "GET":
        return render(request, "app/post_delete.html", {"post": post})
    post.delete()
    return redirect("app:index")


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
    return redirect("app:post_detail", post_id=post_id)


def comment_detail(request, comment_id: int) -> HttpResponse:
    comment = get_object_or_404(Comment, pk=comment_id)
    context = {
        "post": comment.post,
        "comments": [comment],
        "show_prefix": True,
        "max_depth": MAX_DEPTH,
    }
    return render(request, "app/post_detail.html", context)


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
            return redirect("app:post_detail", post_id=reply.post.id)
    else:
        form = CommentForm()
    return render(request, "app/comment_reply.html", {"form": form, "comment": comment})


def comment_delete(request, comment_id: int) -> HttpResponse:
    comment = get_object_or_404(Comment, pk=comment_id)
    if not can_edit(request.user, comment):
        return redirect(settings.LOGIN_URL)

    if request.method == "GET":
        return render(request, "app/comment_delete.html", {"comment": comment})
    elif request.method == "POST":
        comment.delete()
        return redirect("app:post_detail", post_id=comment.post.id)
    return redirect("app:post_detail", post_id=comment.post.id)


def comment_edit(request, comment_id: int) -> HttpResponse:
    comment = get_object_or_404(Comment, pk=comment_id)
    if not can_edit(request.user, comment):
        return redirect(settings.LOGIN_URL)

    if request.method == "POST":
        form = CommentForm(request.POST, instance=comment)
        if form.is_valid():
            comment.save()
            return redirect("app:post_detail", post_id=comment.post.id)
    else:
        form = CommentForm()
    return render(request, "app/comment_edit.html", {"form": form, "comment": comment})


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
    return render(request, "app/comment_history.html", context)


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
    else:
        item.fans.add(request.user)
    item.save()
    return JsonResponse({"success": True, "nlikes": item.nlikes})


def comment_upvote(request, comment_id: int):
    return _upvote(request, comment_id, Comment)


def post_upvote(request, post_id: int):
    return _upvote(request, post_id, Post)
