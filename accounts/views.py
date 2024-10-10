from django.contrib.auth import login as auth_login
from django.contrib.auth import logout as auth_logout
from django.contrib.auth.models import Group
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse

from .forms import CustomUserCreationForm


def logout(request: HttpResponse) -> HttpResponse:
    auth_logout(request)
    return render(request, "registration/logout.html")


def signup(request: HttpResponse) -> HttpResponse:
    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            auth_login(request, user)
            return HttpResponseRedirect(reverse("app:index"))
    else:
        form = CustomUserCreationForm()
    return render(request, "registration/signup.html", {"form": form})
