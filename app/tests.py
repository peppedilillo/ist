"""
TODO: Implement missing tests.

Models Tests:
a. Post Model:

[v] Test creating a post with valid data
[v] Test creating a post with invalid data (e.g., exceeding max length for title)
[v] Test the str method returns the expected string

b. Comment Model:

[v] Test creating a top-level comment
[v] Test creating a nested comment (reply)
[v] Test the str method returns the expected string


Views Tests:
a. Index View:

[v] Test that the index page loads successfully
[v] Test that it displays the correct number of posts (e.g., the latest 5)
[ ] Test the ordering of posts (should be by date, newest first)

b. Post Detail View:

[v] Test that a valid post detail page loads successfully
[v] Test that it displays the correct post information
[v] Test that it displays comments correctly (including nested comments)
[v] Test accessing a non-existent post (should return 404)

c. Post Submit View:

[v] Test submitting a valid post (authenticated user)
[v] Test submitting an invalid post (e.g., missing required fields)
[v] Test accessing the submit page as an unauthenticated user (should redirect to login)

d. Post Edit View:

[v] Test editing a post successfully (by the post author)
[v] Test editing a post by a non-author (should be forbidden)
[v] Test editing with invalid data

e. Post Delete View:

[v] Test deleting a post successfully (by the post author)
[v] Test deleting a post by a non-author (should be forbidden)

f. Comment Views (Reply, Edit, Delete):

[v] Similar tests as for posts, but for comments


Forms Tests:
a. PostForm:

[ ] Test form validation with valid data
[ ] Test form validation with invalid data (e.g., invalid URL)

b. CommentForm:

[ ] Test form validation with valid data
[ ] Test form validation with invalid data (e.g., empty content)


Authentication Tests:
a. Signup:

[ ] Test creating a new account with valid data
[ ] Test creating a new account with invalid data (e.g., mismatched passwords)

b. Login:

[ ] Test logging in with valid credentials
[ ] Test logging in with invalid credentials

c. Logout:

[ ] Test logging out successfully


Permissions and Security Tests:

[ ] Test that unauthenticated users can't access protected views
[ ] Test that users can't edit or delete posts/comments they don't own
[ ] Test CSRF protection on forms


Custom User Model Tests:

[ ] Test creating a user with the custom model
[ ] Test the karma field (if you implement karma functionality)


URL Configuration Tests:

[ ] Test that all URLs resolve to the correct views
[ ] Test that named URLs reverse correctly


Template Tests:

[ ] Test that the correct templates are used for each view
[ ] Test that context variables are correctly passed to templates
"""

from django.contrib.auth import get_user_model
from django.db.utils import DataError
from django.test import TestCase
from django.urls import reverse

from app.models import Comment
from app.models import Post


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


class IndexViewTests(TestCase):
    def setUp(self):
        user = get_user_model().objects.create_user(username="test-user")
        user.save()
        self.user = user

    def test_it_loads(self):
        """page loads successfully"""
        response = self.client.get(reverse("app:index"))
        self.assertEqual(response.status_code, 200)

    def test_no_posts(self):
        """correct message is displayed if no posts"""
        from app.views import EMPTY_MESSAGE

        response = self.client.get(reverse("app:index"))
        self.assertContains(response, EMPTY_MESSAGE)

    def test_nposts(self):
        """the expected number of posts is displayed"""
        from app.views import INDEX_DISPLAY_NPOSTS

        for i in range(31):
            Post(title="title", url="www.google.it", user=self.user).save()

        response = self.client.get(reverse("app:index"))
        self.assertEqual(len(response.context["latest_posts"]), INDEX_DISPLAY_NPOSTS)


class PostDetailViewTests(TestCase):
    def setUp(self):
        user = get_user_model().objects.create_user(username="test-user")
        user.save()
        self.user = user
        post = Post(title="a funny title", url="www.google.it", user=self.user)
        post.save()
        self.post = post

    def test_it_loads(self):
        """page loads successfully"""
        response = self.client.get(reverse("app:post_detail", args=(self.post.pk,)))
        self.assertEqual(response.status_code, 200)

    def test_post_is_there(self):
        """the page contains post informations"""
        response = self.client.get(reverse("app:post_detail", args=(self.post.pk,)))
        self.assertContains(response, self.post.title)
        self.assertContains(response, self.post.url)

    def test_comment_are_displayed(self):
        """the page contains post informations"""
        toplevel_comment = Comment(content="test", post=self.post, parent=None, user=self.user)
        toplevel_comment.save()
        nested_comment = Comment(content="test", post=self.post, parent=None, user=self.user)
        nested_comment.save()

        response = self.client.get(reverse("app:post_detail", args=(self.post.pk,)))
        self.assertContains(response, toplevel_comment.content)
        self.assertContains(response, nested_comment.content)

    def test_non_existent_posts(self):
        """the page contains post informations"""
        response = self.client.get(reverse("app:post_detail", args=(self.post.pk + 1,)))
        self.assertEqual(response.status_code, 404)


class PostSubmitViewTests(TestCase):
    def setUp(self):
        self.logged_user = get_user_model().objects.create_user(username="test-user", password="test-password")

    def test_logged_user_can_post(self):
        post_data = {"title": "title", "url": "https://test.com/"}
        self.client.login(username="test-user", password="test-password")
        response = self.client.post(reverse("app:post_submit"), post_data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Post.objects.count(), 1)

    def test_not_logged_user_can_post(self):
        post_data = {"title": "title", "url": "https://test.com/"}
        response = self.client.post(reverse("app:post_submit"), post_data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Post.objects.count(), 0)

    def test_visitor_submit_redirected_to_login(self):
        response = self.client.get(reverse("app:post_submit"))
        self.assertEqual(response.status_code, 302)  # Check for redirection
        self.assertRedirects(response, f"{reverse('login')}?next={reverse('app:post_submit')}")


class PostEditViewTests(TestCase):
    def setUp(self):
        self.author = get_user_model().objects.create_user(username="test-author", password="test-password")
        self.post = Post.objects.create(title="title", url="wwww.test.com", user=self.author)
        self.lurker = get_user_model().objects.create_user(username="test-lurker", password="test-password")

    def test_author_can_edit(self):
        edit_data = {"title": "updated title"}
        self.client.login(username="test-author", password="test-password")
        response = self.client.post(reverse("app:post_edit", args=(self.post.id,)), edit_data)
        self.assertEqual(response.status_code, 302)
        self.post.refresh_from_db()
        self.assertEqual(self.post.title, edit_data["title"])

    def test_lurker_cant_edit(self):
        edit_data = {"title": "your code sucks"}
        self.client.login(username="test-lurker", password="test-password")
        response = self.client.post(reverse("app:post_edit", args=(self.post.id,)), edit_data)
        self.assertEqual(response.status_code, 302)
        self.post.refresh_from_db()
        self.assertEqual(self.post.title, "title")

    def test_author_edit_invalid_data(self):
        over_max_length = Comment._meta.get_field("content").max_length + 1
        edit_data = {"title": "s" * over_max_length}
        self.client.login(username="test-author", password="test-password")
        response = self.client.post(reverse("app:post_edit", args=(self.post.id,)), edit_data)
        self.assertEqual(response.status_code, 200)
        self.post.refresh_from_db()
        self.assertEqual(self.post.title, "title")


class PostDeleteViewTests(TestCase):
    def setUp(self):
        self.author = get_user_model().objects.create_user(username="test-author", password="test-password")
        self.post = Post.objects.create(title="title", url="wwww.test.com", user=self.author)
        self.lurker = get_user_model().objects.create_user(username="test-lurker", password="test-password")

    def test_author_can_delete(self):
        self.client.login(username="test-author", password="test-password")
        response = self.client.post(reverse("app:post_delete", args=(self.post.id,)))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Post.objects.exists())

    def test_lurker_cant_delete(self):
        self.client.login(username="test-lurker", password="test-password")
        response = self.client.post(reverse("app:post_delete", args=(self.post.id,)))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Post.objects.exists())


class CommentEditViewTests(TestCase):
    def setUp(self):
        self.author = get_user_model().objects.create_user(username="test-author", password="test-password")
        self.post = Post.objects.create(title="title", url="www.test.com", user=self.author)
        self.comment = Comment.objects.create(content="This is a comment", post=self.post, user=self.author)
        self.lurker = get_user_model().objects.create_user(username="test-lurker", password="test-password")

    def test_author_can_edit(self):
        edit_data = {"content": "updated comment"}
        self.client.login(username="test-author", password="test-password")
        response = self.client.post(reverse("app:comment_edit", args=(self.comment.id,)), edit_data)
        self.assertEqual(response.status_code, 302)
        self.comment.refresh_from_db()
        self.assertEqual(self.comment.content, edit_data["content"])

    def test_lurker_cant_edit(self):
        edit_data = {"content": "this is not my comment"}
        self.client.login(username="test-lurker", password="test-password")
        response = self.client.post(reverse("app:comment_edit", args=(self.comment.id,)), edit_data)
        self.assertEqual(response.status_code, 302)
        self.comment.refresh_from_db()
        self.assertEqual(self.comment.content, "This is a comment")

    def test_author_edit_invalid_data(self):
        over_max_length = Comment._meta.get_field("content").max_length + 1
        edit_data = {"content": "s" * over_max_length}  # Assuming max length is 300
        self.client.login(username="test-author", password="test-password")
        response = self.client.post(reverse("app:comment_edit", args=(self.comment.id,)), edit_data)
        self.assertEqual(response.status_code, 200)
        self.comment.refresh_from_db()
        self.assertEqual(self.comment.content, "This is a comment")


class CommentDeleteViewTests(TestCase):
    def setUp(self):
        self.author = get_user_model().objects.create_user(username="test-author", password="test-password")
        self.post = Post.objects.create(title="title", url="www.test.com", user=self.author)
        self.comment = Comment.objects.create(content="This is a comment", post=self.post, user=self.author)
        self.lurker = get_user_model().objects.create_user(username="test-lurker", password="test-password")

    def test_author_can_delete_comment(self):
        self.client.login(username="test-author", password="test-password")
        response = self.client.post(reverse("app:comment_delete", args=(self.comment.id,)))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Comment.objects.filter(id=self.comment.id).exists())

    def test_lurker_cant_delete_comment(self):
        self.client.login(username="test-lurker", password="test-password")
        response = self.client.post(reverse("app:comment_delete", args=(self.comment.id,)))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Comment.objects.filter(id=self.comment.id).exists())
