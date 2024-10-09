from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render, reverse, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST

from .models import Post, Comment
from .forms import PostForm, CommentForm, PostEditForm


def index(request: HttpResponse) -> HttpResponse:
    latest_posts = Post.objects.order_by("-date")[:5]
    context = {"latest_posts": latest_posts}
    return render(request, "app/index.html", context)


def post_detail(request: HttpResponse, post_id: int) -> HttpResponse:
    post = get_object_or_404(Post, pk=post_id)
    comments = post.comments.filter(parent=None).order_by("-created_at")
    comment_form = CommentForm()
    context = {
        "post": post,
        "comments": comments,
        "comment_form": comment_form,
    }
    return render(request, "app/post_detail.html", context)


@login_required
def post_submit(request: HttpResponse) -> HttpResponse:
    if request.method == "POST":
        form = PostForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.user = request.user
            post.save()
            return redirect("app:index")
    else:
        form = PostForm()
    return render(request, 'app/post_submit.html', {'form': form})


@login_required
def post_edit(request: HttpResponse, post_id: int) -> HttpResponse:
    post = get_object_or_404(Post, pk=post_id)
    if request.user != post.user:
        redirect("app:detail", post_id=post_id)

    if request.method == "POST":
        form = PostEditForm(request.POST, instance=post)
        if form.is_valid():
            # post.title = form.cleaned_data.get('title')
            post.save()
            return redirect("app:detail", post_id=post.id)
    else:
        form = PostEditForm()
    return render(request, "app/post_edit.html", {"form": form, "post": post})


@login_required
def post_delete(request: HttpResponse, post_id: int) -> HttpResponse:
    post = get_object_or_404(Post, pk=post_id)
    if request.user != post.user:
        redirect("app:detail", post_id=post_id)

    if request.method == "GET":
        return render(request, "app/post_delete.html", {"post": post})
    elif request.method == "POST":
        post.delete()
        return redirect('app:index')
    redirect("app:detail", post_id=post_id)


@login_required
@require_POST
def post_comment(request: HttpResponse, post_id: int) -> HttpResponse:
    """Adds a top level comment to a post."""
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.post = post
        comment.user = request.user
        comment.parent = None
        comment.save()
    return redirect('app:detail', post_id=post_id)


@login_required
@require_POST
def comment_reply(request: HttpResponse, parent_comment_id: int) -> HttpResponse:
    """Adds a reply to a comment."""
    parent_comment = get_object_or_404(Comment, pk=parent_comment_id)
    form = CommentForm(request.POST)
    if form.is_valid():
        comment = form.save(commit = False)
        comment.post = parent_comment.post
        comment.user = request.user
        comment.parent = parent_comment
        comment.save()
    return redirect("app:detail", post_id=comment.post.id)


@login_required
def comment_delete(request: HttpResponse, comment_id: int) -> HttpResponse:
    comment = get_object_or_404(Comment, pk=comment_id)
    if request.user != comment.user:
        redirect("app:detail", post_id=comment.post.id)

    if request.method == "GET":
        return render(request, "app/comment_delete.html", {"comment": comment})
    elif request.method == "POST":
        comment.delete()
        return redirect("app:detail", post_id=comment.post.id)
    redirect("app:detail", post_id=comment.post.id)


@login_required
def comment_edit(request: HttpResponse, comment_id: int) -> HttpResponse:
    comment = get_object_or_404(Comment, pk=comment_id)
    if request.user != comment.user:
        redirect("app:detail", post_id=comment.post.id)

    if request.method == "POST":
        form = CommentForm(request.POST, instance=comment)
        if form.is_valid():
            # comment.content =  form.cleaned_data.get('content')
            comment.save()
            return redirect("app:detail", post_id=comment.post.id)
    else:
        form = CommentForm()
    return render(request, "app/comment_edit.html", {"form": form, "comment": comment})
