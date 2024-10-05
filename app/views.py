from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render, reverse, redirect
from django.contrib.auth.decorators import login_required

from . import models
from .forms import PostForm


def index(request: HttpResponse) -> HttpResponse:
    latest_posts = models.Post.objects.order_by("-date")[:5]
    context = {"latest_posts": latest_posts}
    return render(request, "app/index.html", context)


def detail(request: HttpResponse, post_id: int) -> HttpResponse:
    post = get_object_or_404(models.Post, pk=post_id)
    return HttpResponse(f"{post.title} {post.url} ({post.date})")


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
