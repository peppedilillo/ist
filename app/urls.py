from django.urls import path

from . import views

paths = [path("", views.index, name="index")]
