from django.apps import apps
from django.contrib.auth import login as auth_login
from django.contrib.auth import logout as auth_logout
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse

from .forms import CustomUserCreationForm

Post = apps.get_model("mboard", "Post")
Comment = apps.get_model("mboard", "Comment")


def logout(request):
    auth_logout(request)
    return render(request, "registration/logout.html")


def signup(request):
    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            auth_login(request, user)
            return HttpResponseRedirect(reverse("mboard:index"))
    else:
        form = CustomUserCreationForm()
    return render(request, "registration/signup.html", {"form": form})
