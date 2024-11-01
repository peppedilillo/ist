"""
Authentication Tests:
a. Signup:

[v] Test creating a new account with valid data
[v] Test creating a new account with invalid data (e.g., mismatched passwords)

b. Login:

[v] Test logging in with valid credentials
[v] Test logging in with invalid credentials

c. Logout:

[v] Test logging out successfully
"""
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse


# Create your tests here.
class CustomUserModelTests(TestCase):
    def setUp(self):
        # Create an authenticated user and a post
        self.user = get_user_model().objects.create_user(username="test-user", password="test-password")

    def test_create_user_with_custom_model(self):
        self.assertEqual(self.user.username, "test-user")
        self.assertTrue(self.user.check_password("test-password"))
        self.assertTrue(self.user.is_active)
        self.assertFalse(self.user.is_staff)
        self.assertFalse(self.user.is_superuser)


class SignupTests(TestCase):
    def test_create_account_with_valid_data(self):
        form_data = {
            "username": "test-user",
            "password1": "validpassword123",
            "password2": "validpassword123",
        }
        response = self.client.post(reverse("accounts:signup"), form_data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(get_user_model().objects.filter(username=form_data["username"]).exists())

    def test_create_account_with_mismatched_passwords(self):
        form_data = {
            "username": "test-user",
            "password1": "validpassword123",
            "password2": "invalidpassword123",  # Mismatched passwords
        }
        response = self.client.post(reverse("accounts:signup"), form_data)
        self.assertEqual(response.status_code, 200)  # form should re-render with error
        self.assertFalse(get_user_model().objects.filter(username=form_data["username"]).exists())
        self.assertContains(response, "password fields didn’t match.")


class LoginTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="test-user", password="test-password")

    def test_login_with_valid_credentials(self):
        form_data = {
            "username": "test-user",
            "password": "test-password",
        }
        response = self.client.post(reverse("login"), form_data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.wsgi_request.user.is_authenticated)

    def test_login_with_invalid_password(self):
        form_data = {
            "username": "test-user",
            "password": "wrongpassword",  # Invalid password
        }
        response = self.client.post(reverse("login"), form_data)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.wsgi_request.user.is_authenticated)
        self.assertContains(response, "Please enter a correct username and password.")


class LogoutTests(TestCase):
    def setUp(self):
        # Create and log in the user for logout tests
        self.user = get_user_model().objects.create_user(username="test-user", password="test-password")
        self.client.login(username="test-user", password="test-password")

    def test_logout_successfully(self):
        response = self.client.get(reverse("logout"))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.wsgi_request.user.is_authenticated)
        self.assertContains(response, "Logged out")
