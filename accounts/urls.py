from django.urls import path

from . import views

app_name = "accounts"
urlpatterns = [
    path("signup/", views.signup, name="signup"),
    path("logout/", views.logout, name="logout"),
    path("<int:user_id>/", views.profile, name="profile"),
]
