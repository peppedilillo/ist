"""
Forms Tests:
a. PostForm:

[v] Test form validation with valid data
[v] Test form validation with invalid data (e.g., invalid URL)

b. CommentForm:

[v] Test form validation with valid data
[v] Test form validation with invalid data (e.g., empty content)

"""
from django.test import TestCase

from app.forms import PostForm, CommentForm


class PostFormTests(TestCase):
    def test_form_valid_data(self):
        form_data = {"title": "title", "url": "https://example.com"}
        form = PostForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_form_invalid_url(self):
        form_data = {"title": "title", "url": "_"}
        invalid_urls = [
            "invalid_url",
            "ww.invalid_url.com",
            "htp://www.invalid_url.com",
        ]
        for url in invalid_urls:
            form_data["url"] = url
            form = PostForm(data=form_data)
            self.assertFalse(form.is_valid())
            self.assertIn("url", form.errors)


class CommentFormTests(TestCase):
    def test_form_valid_data(self):
        form_data = {"content": "This is a valid comment."}
        form = CommentForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_form_invalid_empty_content(self):
        form_data = {"title": "title", "url": "_"}
        invalid_comments = [
            "",
        ]
        for invalid_comment in invalid_comments:
            form_data["content"] = invalid_comment
            form = CommentForm(data=form_data)
            self.assertFalse(form.is_valid())
            self.assertIn("content", form.errors)
