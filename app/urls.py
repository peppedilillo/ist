from django.urls import path, include

from . import views

app_name = "app"
urlpatterns = [
    path("", views.index, name="index"),
    path("posts/<int:post_id>/", views.detail, name="detail"),
    path("posts/<int:post_id>/comment", views.post_comment, name="add_comment"),
    path("posts/<int:post_id>/delete", views.post_delete, name="post_delete"),
    path("comments/<int:parent_comment_id>/reply", views.comment_reply, name="reply"),
    path("comments/<int:comment_id>/delete", views.comment_delete, name="comment_delete"),
    path("submit/", views.submit, name="submit"),
]
