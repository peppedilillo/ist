from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render, reverse, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.core.exceptions import ValidationError

from . import models
from .forms import PostForm, CommentForm


def index(request: HttpResponse) -> HttpResponse:
    latest_posts = models.Post.objects.order_by("-date")[:5]
    context = {"latest_posts": latest_posts}
    return render(request, "app/index.html", context)


def detail(request: HttpResponse, post_id: int) -> HttpResponse:
    post = get_object_or_404(models.Post, pk=post_id)
    print(post.url)
    comments = post.comments.order_by("-created_at")
    comment_form = CommentForm()
    context = {
        "post": post,
        "comments": comments,
        "comment_form": comment_form,
    }
    return render(request, "app/detail.html", context)


@login_required
@require_POST
def add_comment(request, post_id):
    post = get_object_or_404(models.Post, pk=post_id)
    form = CommentForm(request.POST)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.post = post
        comment.user = request.user
        comment.save()
    return redirect('app:detail', post_id=post_id)


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
