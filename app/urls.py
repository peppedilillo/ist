from django.urls import path

from . import views

app_name = "app"
urlpatterns = [
    path("", views.index, name="index"),
    path("posts/<int:post_id>/", views.post_detail, name="detail"),
    path("posts/<int:post_id>/comment", views.post_comment, name="add_comment"),
    path("posts/<int:post_id>/delete", views.post_delete, name="post_delete"),
    path("posts/<int:post_id>/edit", views.post_edit, name="post_edit"),
    path("comments/<int:parent_comment_id>/reply", views.comment_reply, name="reply"),
    path(
        "comments/<int:comment_id>/delete", views.comment_delete, name="comment_delete"
    ),
    path("comments/<int:comment_id>/edit", views.comment_edit, name="comment_edit"),
    path("submit/", views.post_submit, name="submit"),
]
