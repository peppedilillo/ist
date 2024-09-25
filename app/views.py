from django.shortcuts import render
from django.http import HttpResponse
from django.shortcuts import get_object_or_404

from . import models


def index(request: HttpResponse) -> HttpResponse:
    latest_posts = models.Post.objects.order_by("-date")[:5]
    latest_posts_titles = [p.title for p in latest_posts]
    return HttpResponse(", ".join(latest_posts_titles))


def detail(request: HttpResponse, post_id: int) -> HttpResponse:
    post = get_object_or_404(models.Post, pk=post_id)
    return HttpResponse(f"{post.title} {post.url} ({post.date})")
