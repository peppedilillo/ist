from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render, reverse, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST

from .models import Post, Comment
from .forms import PostForm, CommentForm


def index(request: HttpResponse) -> HttpResponse:
    latest_posts = Post.objects.order_by("-date")[:5]
    context = {"latest_posts": latest_posts}
    return render(request, "app/index.html", context)


def detail(request: HttpResponse, post_id: int) -> HttpResponse:
    post = get_object_or_404(Post, pk=post_id)
    comments = post.comments.filter(parent=None).order_by("-created_at")
    comment_form = CommentForm()
    context = {
        "post": post,
        "comments": comments,
        "comment_form": comment_form,
    }
    return render(request, "app/detail.html", context)


@login_required
def submit(request: HttpResponse) -> HttpResponse:
    if request.method == "POST":
        form = PostForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.user = request.user
            post.save()
            return redirect("app:index")
    else:
        form = PostForm()
    return render(request, 'app/submit.html', {'form': form})


@login_required
@require_POST
def add_comment(request: HttpResponse, post_id: int) -> HttpResponse:
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
def reply(request: HttpResponse, parent_comment_id: int) -> HttpResponse:
    parent_comment = get_object_or_404(Comment, pk=parent_comment_id)
    form = CommentForm(request.POST)
    if form.is_valid():
        comment = form.save(commit = False)
        comment.post = parent_comment.post
        comment.user = parent_comment.user
        comment.parent = parent_comment
        comment.save()
    return redirect("app:detail", post_id=comment.post.id)
