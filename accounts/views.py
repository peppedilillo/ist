from django.contrib.auth import login
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse
from django.shortcuts import render
from django.contrib.auth.models import Group

from .forms import CustomUserCreationForm


def signup(request: HttpResponse) -> HttpResponse:
    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            user.groups.add(Group.objects.get(name="user"))
            login(request, user)
            return HttpResponseRedirect(reverse("app:index"))
    else:
        form = CustomUserCreationForm()
    return render(request, "registration/signup.html", {"form": form})
