from django.urls import path

from . import views

app_name = "mboard"
urlpatterns = [
    path("", views.index, name="index"),
    path("news/", views.news, name="news"),
    path("papers/", views.papers, name="papers"),
    path("code/", views.code, name="code"),
    path("jobs/", views.jobs, name="jobs"),
    path("posts/<int:post_id>/", views.post_detail, name="post_detail"),
    path("posts/submit/", views.post_submit, name="post_submit"),
    path("posts/<int:post_id>/comment", views.post_comment, name="post_comment"),
    path("posts/<int:post_id>/delete", views.post_delete, name="post_delete"),
    path("posts/<int:post_id>/edit", views.post_edit, name="post_edit"),
    path("posts/<int:post_id>/upvote", views.post_upvote, name="post_upvote"),
    path("posts/<int:post_id>/pin", views.post_pin, name="post_pin"),
    path("comments/<int:comment_id>/", views.comment_detail, name="comment_detail"),
    path("comments/<int:comment_id>/reply", views.comment_reply, name="comment_reply"),
    path("comments/<int:comment_id>/delete", views.comment_delete, name="comment_delete"),
    path("comments/<int:comment_id>/edit", views.comment_edit, name="comment_edit"),
    path("comments/<int:comment_id>/history", views.comment_history, name="comment_history"),
    path("comments/<int:comment_id>/upvote", views.comment_upvote, name="comment_upvote"),
    path("accounts/<int:user_id>/", views.profile, name="profile"),
    path("accounts/<int:user_id>/posts", views.profile_posts, name="profile_posts"),
    path("accounts/<int:user_id>/comments", views.profile_comments, name="profile_comments"),
]
