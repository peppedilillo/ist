from django.contrib.auth import login
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse
from django.shortcuts import render
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import Group


def signup(request: HttpResponse) -> HttpResponse:
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            user.groups.add(Group.objects.get(name="user"))
            login(request, user)
            return HttpResponseRedirect(reverse("app:index"))
    else:
        form = UserCreationForm()
    return render(request, "registration/signup.html", {"form": form})
