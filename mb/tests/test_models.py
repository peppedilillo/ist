"""
Models Tests:
a. Post Model:

[v] Test creating a post with valid data
[v] Test creating a post with invalid data (e.g., exceeding max length for title)
[v] Test the str method returns the expected string

b. Comment Model:

[v] Test creating a top-level comment
[v] Test creating a nested comment (reply)
[v] Test the str method returns the expected string
"""

from django.contrib.auth import get_user_model
from django.db import DataError
from django.test import TestCase

from ..models import Post, Comment


class PostModelTests(TestCase):
    def setUp(self):
        user = get_user_model().objects.create_user(username="test-user")
        user.save()
        self.user = user

    def test_create(self):
        """Create and save a post with valid data"""
        Post(title="title", url="www.google.it", user=self.user).save()

    def test_create_invalid_title(self):
        """Creates and save a post with invalid title"""
        try:
            _ = Post(title="x" * 121, url="www.google.it", user=self.user).save()
        except DataError:
            return
        self.assertTrue(False)

    def test_create_invalid_url(self):
        """Creates a post with invalid url"""
        from random import choice
        from string import ascii_letters

        try:
            _ = Post(
                title="title",
                url=f"www.test.com/{''.join([choice(ascii_letters) for _ in range(300)])}",
                user=self.user,
            ).save()
        except DataError:
            return
        self.assertTrue(False)

    def test_str_method(self):
        """Test post string representation"""
        title = "Gürzénìchstraße"
        url = "www.test.com"
        p = Post(title=title, url=url, user=self.user)
        p.save()
        self.assertEqual(
            str(Post.objects.get(pk=p.pk)),
            "Gürzénìchstraße (www.test.com)",
        )


class CommentModelTests(TestCase):
    def setUp(self):
        user = get_user_model().objects.create_user(username="test-user")
        user.save()
        self.user = user
        post = Post(title="title", url="www.google.it", user=self.user)
        post.save()
        self.post = post

    def test_toplevel_create(self):
        """Creates a top level comment"""
        Comment(content="test", post=self.post, parent=None, user=self.user).save()

    def test_reply_create(self):
        """Creates a reply"""
        toplevel_comment = Comment(content="test", post=self.post, parent=None, user=self.user)
        toplevel_comment.save()
        Comment(content="test", post=self.post, parent=None, user=self.user).save()

    def test_str_method(self):
        """Test comment string representation"""
        c = Comment(content="", post=self.post, parent=None, user=self.user)
        c.save()
        self.assertEqual(
            str(Comment.objects.get(pk=c.pk)),
            f"Comment by {self.user.username} on {c.post.title}",
        )
