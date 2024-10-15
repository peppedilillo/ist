from collections import namedtuple

from django.contrib.auth import login as auth_login, get_user
from django.contrib.auth import logout as auth_logout
from django.contrib.auth import get_user_model
from django.core.paginator import Paginator
from django.http import HttpResponseRedirect
from django.shortcuts import render, get_object_or_404
from django.urls import reverse
from django.apps import apps

from .forms import CustomUserCreationForm
from typing import NamedTuple

Post = apps.get_model("app", "Post")
Comment = apps.get_model("app", "Comment")

EMPTY_MESSAGE = "It is empty here!"
PROFILE_NENTRIES = 30


def logout(request):
    auth_logout(request)
    return render(request, "registration/logout.html")


def signup(request):
    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            auth_login(request, user)
            return HttpResponseRedirect(reverse("app:index"))
    else:
        form = CustomUserCreationForm()
    return render(request, "registration/signup.html", {"form": form})


class Content(NamedTuple):
    content: str
    ispost: bool


def annotated(contributions: list[Post | Comment]):
    annotated_contributions = [
        Content(contribution, isinstance(contribution, Post))
        for contribution in contributions
    ]
    return annotated_contributions


def profile(request, user_id: int):
    user = get_object_or_404(get_user_model(), pk=user_id)
    paginator = Paginator(annotated(user.contributions()), PROFILE_NENTRIES)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    context = {
        "user": user,
        "page_obj": page_obj,
        "empty_message": EMPTY_MESSAGE,
    }
    return render(request, "accounts/profile.html", context)
