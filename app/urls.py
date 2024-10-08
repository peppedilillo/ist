from django.urls import path, include

from . import views

app_name = "app"
urlpatterns = [
    path("", views.index, name="index"),
    path("posts/<int:post_id>/", views.detail, name="detail"),
    path("posts/<int:post_id>/comment", views.add_comment, name="add_comment"),
    path("comments/<int:parent_comment_id>/reply", views.reply, name="reply"),
    path("submit/", views.submit, name="submit"),
]
