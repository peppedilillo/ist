from django.urls import path

from . import views

app_name = "app"
urlpatterns = [
    path("", views.index, name="index"),
    path("papers/", views.papers, name="papers"),
    path("code/", views.code, name="code"),
    path("jobs/", views.jobs, name="jobs"),
    path("posts/<int:post_id>/", views.post_detail, name="post_detail"),
    path("posts/submit/", views.post_submit, name="post_submit"),
    path("posts/<int:post_id>/comment", views.post_comment, name="post_comment"),
    path("posts/<int:post_id>/delete", views.post_delete, name="post_delete"),
    path("posts/<int:post_id>/edit", views.post_edit, name="post_edit"),
    path("comments/<int:comment_id>/", views.comment_detail, name="comment_detail"),
    path("comments/<int:comment_id>/reply", views.comment_reply, name="comment_reply"),
    path("comments/<int:comment_id>/delete", views.comment_delete, name="comment_delete"),
    path("comments/<int:comment_id>/edit", views.comment_edit, name="comment_edit"),
]
