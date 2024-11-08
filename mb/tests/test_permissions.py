"""
Permissions and Security Tests:

[v] Test that unauthenticated users can't access protected views
[v] Test CSRF protection on forms


Custom User Model Tests:

[v] Test creating a user with the custom model
[v] Test the karma field (if you implement karma functionality)


Ratelimits Tests

[v] Test that rate limiter works for post submits
[v] Test that rate limiter works for post upvotes
[ ] Repeat for above but for comments.
"""

import re

from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.urls import reverse

from ..middleware import AUTHENTICATED_LIMIT
from ..models import Post


class PermissionsAndSecurityTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="test-user", password="test-password"
        )
        self.post = Post.objects.create(
            title="test post", url="https://example.com", user=self.user
        )

    def test_unauthenticated_user_cannot_access_protected_views(self):
        self.client = Client()
        protected_urls = [
            reverse("mb:post_edit", args=[self.post.id]),
            reverse("mb:post_delete", args=[self.post.id]),
            reverse("mb:post_submit"),
        ]
        for url in protected_urls:
            response = self.client.get(url)
            self.assertEqual(response.status_code, 302)
            self.assertTrue(response.url.startswith(reverse("login")))

    def test_post_templates_contains_token(self):
        pattern = r"<form[^>]*>\s*{%\s*csrf_token\s*%}"

        post_templates = [
            "comment_edit.html",
            "comment_reply.html",
            "post_delete.html",
            "post_detail.html",
            "post_edit.html",
            "post_submit.html",
        ]
        for template in post_templates:
            with open(f"mb/templates/mb/{template}") as f:
                content = "".join(f.readlines())
            match = re.search(pattern, content)
            self.assertIsNotNone(match)


class RateLimiterTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="test-user", password="test-password"
        )
        self.client = Client()
        self.client.login(username="test-user", password="test-password")
        self.post_data = {"title": f"test", "url": "www.test.com"}

    def test_repeated_post(self):
        for i in range(AUTHENTICATED_LIMIT + 1):
            response = self.client.post(reverse("mb:post_submit"), data=self.post_data)
            if i < AUTHENTICATED_LIMIT:
                self.assertEqual(response.status_code, 302)
            else:
                self.assertEqual(response.status_code, 429)

    def test_repeated_upvote(self):
        post = Post.objects.create(**self.post_data, user=self.user)
        for i in range(AUTHENTICATED_LIMIT + 1):
            response = self.client.post(reverse("mb:post_upvote", args=(post.id,)))
            if i < AUTHENTICATED_LIMIT:
                self.assertEqual(response.status_code, 200)
            else:
                self.assertEqual(response.status_code, 429)
