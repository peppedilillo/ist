from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render, reverse

from . import models


def index(request: HttpResponse) -> HttpResponse:
    latest_posts = models.Post.objects.order_by("-date")[:5]
    context = {"latest_posts": latest_posts}
    return render(request, "app/index.html", context)


def detail(request: HttpResponse, post_id: int) -> HttpResponse:
    post = get_object_or_404(models.Post, pk=post_id)
    return HttpResponse(f"{post.title} {post.url} ({post.date})")


def check_submission(title: str, url: str, text: str) -> bool:
    if title and url and text:
        return True
    return False


def submit(request: HttpResponse) -> HttpResponse:
    if request.method == 'POST':

        title = request.POST['title'].strip()
        url = request.POST['url']
        text = request.POST['text'].strip()

        if not check_submission(title, url, text):
            return render(request, 'app/submit.html', context={'errors': True})

        post = models.Post(title=title, url=url)
        post.save()
        return HttpResponseRedirect(reverse("app:index"))

    else:
        return render(request, 'app/submit.html')