from django.shortcuts import render, HttpResponse, HttpResponseRedirect, reverse
from django.contrib.auth.forms import UserCreationForm


def signup(request: HttpResponse) -> HttpResponse:
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse("app:index"))
    else:
        form = UserCreationForm()
    return render(request, "registration/login.html", {"form": form})
