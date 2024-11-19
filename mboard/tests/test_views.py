"""
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
[v] Author gets form by get method
[v] Lurker gets redirected attempting get

d. Post Edit View:

[v] Test editing a post successfully (by the post author)
[v] Test editing a post by a non-author (should be forbidden)
[v] Test editing with invalid data
[v] Author gets form by get method
[v] Lurker gets redirected attempting get

e. Post Delete View:

[v] Test deleting a post successfully (by the post author)
[v] Test deleting a post by a non-author (should be forbidden)

f. Post Comment View:

[v] Test creating a top-level comment successfully (by authenticated user)
[v] Test failing to create a top-level comment (by visitor)

g. Comment Views (Reply, Edit, Delete):

[~] Similar tests as for posts, but for comments

h. Post Pinning:

[v] test only admin, moderators and users are able to access pin page and pin a post.
[v] test pinning and then unpinning behaves as intended.
[v] test pinning not existent post results in 404.

g. Comment Detail View:

[v] Test detail view loads successfully for valid comment
[v] Test detail view returns 404 for invalid comment
[v] Test nested replies are properly included
[v] Test max depth nesting behavior
[v] Test post context is included in view
[v] Test fan status for authenticated users
[v] Test proper ordering of nested comments with no likes
"""

from django.contrib.auth import get_user_model
from django.test import Client
from django.test import TestCase
from django.urls import reverse

from ..models import Comment
from ..models import Post
from ..settings import MAX_DEPTH


class IndexViewTests(TestCase):
    def setUp(self):
        user = get_user_model().objects.create_user(username="test-user")
        user.save()
        self.user = user

    def test_it_loads(self):
        """page loads successfully"""
        response = self.client.get(reverse("mboard:index"))
        self.assertEqual(response.status_code, 200)

    def test_no_posts(self):
        """correct message is displayed if no posts"""
        from ..views import EMPTY_MESSAGE

        response = self.client.get(reverse("mboard:index"))
        self.assertContains(response, EMPTY_MESSAGE)

    def test_nposts(self):
        """the expected number of posts is displayed"""
        from ..settings import INDEX_NPOSTS

        for i in range(31):
            Post(title="title", url="www.google.it", user=self.user).save()

        response = self.client.get(reverse("mboard:index"))
        self.assertEqual(len(response.context["latest_posts"]), INDEX_NPOSTS)


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
        response = self.client.get(reverse("mboard:post_detail", args=(self.post.pk,)))
        self.assertEqual(response.status_code, 200)

    def test_post_is_there(self):
        """the page contains post informations"""
        response = self.client.get(reverse("mboard:post_detail", args=(self.post.pk,)))
        self.assertContains(response, self.post.title)
        self.assertContains(response, self.post.url)

    def test_comment_are_displayed(self):
        """the page contains post informations"""
        toplevel_comment = Comment(content="test", post=self.post, parent=None, user=self.user)
        toplevel_comment.save()
        nested_comment = Comment(content="test", post=self.post, parent=None, user=self.user)
        nested_comment.save()

        response = self.client.get(reverse("mboard:post_detail", args=(self.post.pk,)))
        self.assertContains(response, toplevel_comment.content)
        self.assertContains(response, nested_comment.content)

    def test_non_existent_posts(self):
        """the page contains post informations"""
        response = self.client.get(reverse("mboard:post_detail", args=(self.post.pk + 1,)))
        self.assertEqual(response.status_code, 404)


class PostSubmitViewTests(TestCase):
    def setUp(self):
        self.logged_user = get_user_model().objects.create_user(username="test-user", password="test-password")

    def test_logged_user_can_post(self):
        post_data = {"title": "title", "url": "https://test.com/"}
        self.client.login(username="test-user", password="test-password")
        response = self.client.post(reverse("mboard:post_submit"), post_data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Post.objects.count(), 1)

    def test_not_logged_user_can_post(self):
        post_data = {"title": "title", "url": "https://test.com/"}
        response = self.client.post(reverse("mboard:post_submit"), post_data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Post.objects.count(), 0)

    def test_visitor_submit_redirected_to_login(self):
        response = self.client.get(reverse("mboard:post_submit"))
        self.assertEqual(response.status_code, 302)  # Check for redirection
        self.assertRedirects(response, f"{reverse('login')}?next={reverse('mboard:post_submit')}")

    def test_post_submit_template_on_get(self):
        self.client.login(username="test-user", password="test-password")
        response = self.client.get(reverse("mboard:post_submit"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "mboard/post_submit.html")


class PostEditViewTests(TestCase):
    def setUp(self):
        self.author = get_user_model().objects.create_user(username="test-author", password="test-password")
        self.post = Post.objects.create(title="title", url="wwww.test.com", user=self.author)
        self.lurker = get_user_model().objects.create_user(username="test-lurker", password="test-password")

    def test_author_can_edit(self):
        edit_data = {"title": "updated title"}
        self.client.login(username="test-author", password="test-password")
        response = self.client.post(reverse("mboard:post_edit", args=(self.post.id,)), edit_data)
        self.assertEqual(response.status_code, 302)
        self.post.refresh_from_db()
        self.assertEqual(self.post.title, edit_data["title"])

    def test_lurker_cant_edit(self):
        edit_data = {"title": "your code sucks"}
        self.client.login(username="test-lurker", password="test-password")
        response = self.client.post(reverse("mboard:post_edit", args=(self.post.id,)), edit_data)
        self.assertEqual(response.status_code, 302)
        self.post.refresh_from_db()
        self.assertEqual(self.post.title, "title")

    def test_author_edit_invalid_data(self):
        over_max_length = Comment._meta.get_field("content").max_length + 1
        edit_data = {"title": "s" * over_max_length}
        self.client.login(username="test-author", password="test-password")
        response = self.client.post(reverse("mboard:post_edit", args=(self.post.id,)), edit_data)
        self.assertEqual(response.status_code, 200)
        self.post.refresh_from_db()
        self.assertEqual(self.post.title, "title")

    def test_author_gets_valid_form(self):
        self.client.login(username="test-author", password="test-password")
        response = self.client.get(reverse("mboard:post_edit", args=[self.post.id]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "mboard/post_edit.html")  # Check that the correct template is used

    def test_lurker_gets_redirected(self):
        response = self.client.get(reverse("mboard:post_edit", args=[self.post.id]))
        self.client.login(username="test-lurker", password="test-password")
        self.assertEqual(response.status_code, 302)


class PostDeleteViewTests(TestCase):
    def setUp(self):
        self.author = get_user_model().objects.create_user(username="test-author", password="test-password")
        self.post = Post.objects.create(title="title", url="wwww.test.com", user=self.author)
        self.lurker = get_user_model().objects.create_user(username="test-lurker", password="test-password")

    def test_author_can_delete(self):
        self.client.login(username="test-author", password="test-password")
        response = self.client.post(reverse("mboard:post_delete", args=(self.post.id,)))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Post.objects.exists())

    def test_lurker_cant_delete(self):
        self.client.login(username="test-lurker", password="test-password")
        response = self.client.post(reverse("mboard:post_delete", args=(self.post.id,)))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Post.objects.exists())

    def test_author_gets_valid_form(self):
        self.client.login(username="test-author", password="test-password")
        response = self.client.get(reverse("mboard:post_delete", args=[self.post.id]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "mboard/post_delete.html")  # Check that the correct template is used

    def test_lurker_gets_redirected(self):
        response = self.client.get(reverse("mboard:post_delete", args=[self.post.id]))
        self.client.login(username="test-lurker", password="test-password")
        self.assertEqual(response.status_code, 302)


class PostCommentViewTests(TestCase):
    def setUp(self):
        self.author = get_user_model().objects.create_user(username="test-author", password="test-password")
        self.post = Post.objects.create(title="title", url="www.test.com", user=self.author)
        self.commenter = get_user_model().objects.create_user(username="test-commenter", password="test-password")

    def test_user_can_post_toplevel_comment(self):
        self.client.login(username="test-commenter", password="test-password")
        response = self.client.post(
            reverse("mboard:post_comment", args=(self.post.id,)),
            {"content": "test comment"},
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Post.objects.get(id=self.post.id).comments.exists())

    def test_visitor_cant_post_toplevel_comment(self):
        response = self.client.post(
            reverse("mboard:post_comment", args=(self.post.id,)),
            {"content": "test comment"},
        )
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Post.objects.get(id=self.post.id).comments.exists())


class CommentEditViewTests(TestCase):
    def setUp(self):
        self.author = get_user_model().objects.create_user(username="test-author", password="test-password")
        self.post = Post.objects.create(title="title", url="www.test.com", user=self.author)
        self.comment = Comment.objects.create(content="This is a comment", post=self.post, user=self.author)
        self.lurker = get_user_model().objects.create_user(username="test-lurker", password="test-password")

    def test_author_can_edit(self):
        edit_data = {"content": "updated comment"}
        self.client.login(username="test-author", password="test-password")
        response = self.client.post(reverse("mboard:comment_edit", args=(self.comment.id,)), edit_data)
        self.assertEqual(response.status_code, 302)
        self.comment.refresh_from_db()
        self.assertEqual(self.comment.content, edit_data["content"])

    def test_lurker_cant_edit(self):
        edit_data = {"content": "this is not my comment"}
        self.client.login(username="test-lurker", password="test-password")
        response = self.client.post(reverse("mboard:comment_edit", args=(self.comment.id,)), edit_data)
        self.assertEqual(response.status_code, 302)
        self.comment.refresh_from_db()
        self.assertEqual(self.comment.content, "This is a comment")

    def test_author_edit_invalid_data(self):
        over_max_length = Comment._meta.get_field("content").max_length + 1
        edit_data = {"content": "s" * over_max_length}  # Assuming max length is 300
        self.client.login(username="test-author", password="test-password")
        response = self.client.post(reverse("mboard:comment_edit", args=(self.comment.id,)), edit_data)
        self.assertEqual(response.status_code, 200)
        self.comment.refresh_from_db()
        self.assertEqual(self.comment.content, "This is a comment")

    def test_author_gets_valid_form(self):
        self.client.login(username="test-author", password="test-password")
        response = self.client.get(reverse("mboard:comment_edit", args=[self.comment.id]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "mboard/comment_edit.html")

    def test_lurker_gets_redirected(self):
        response = self.client.get(reverse("mboard:comment_edit", args=[self.comment.id]))
        self.client.login(username="test-lurker", password="test-password")
        self.assertEqual(response.status_code, 302)


class CommentDeleteViewTests(TestCase):
    def setUp(self):
        self.author = get_user_model().objects.create_user(username="test-author", password="test-password")
        self.post = Post.objects.create(title="title", url="www.test.com", user=self.author)
        self.comment = Comment.objects.create(content="This is a comment", post=self.post, user=self.author)
        self.lurker = get_user_model().objects.create_user(username="test-lurker", password="test-password")

    def test_author_can_delete_comment(self):
        self.client.login(username="test-author", password="test-password")
        response = self.client.post(reverse("mboard:comment_delete", args=(self.comment.id,)))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Comment.objects.filter(id=self.comment.id).exists())

    def test_lurker_cant_delete_comment(self):
        self.client.login(username="test-lurker", password="test-password")
        response = self.client.post(reverse("mboard:comment_delete", args=(self.comment.id,)))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Comment.objects.filter(id=self.comment.id).exists())

    def test_author_gets_valid_form(self):
        self.client.login(username="test-author", password="test-password")
        response = self.client.get(reverse("mboard:comment_delete", args=[self.comment.id]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "mboard/comment_delete.html")  # Check that the correct template is used

    def test_lurker_gets_redirected(self):
        response = self.client.get(reverse("mboard:comment_delete", args=[self.comment.id]))
        self.client.login(username="test-lurker", password="test-password")
        self.assertEqual(response.status_code, 302)


class PostPinTests(TestCase):
    def setUp(self):
        self.admin = get_user_model().objects.create_user(
            username="test-admin",
            password="test-password",
            status="a",
        )
        self.moderator = get_user_model().objects.create_user(
            username="test-moderator",
            password="test-password",
            status="m",
        )
        self.regular_user = get_user_model().objects.create_user(
            username="test-user",
            password="test-password",
            status="u",
        )
        self.banned_user = get_user_model().objects.create_user(
            username="test-banned",
            password="test-password",
            status="b",
        )
        self.post = Post.objects.create(title="Test Post", url="https://example.com", user=self.regular_user)
        self.pin_url = reverse("mboard:post_pin", args=[self.post.id])
        self.client = Client()

    def test_admin_can_access_pin_page(self):
        self.client.login(username="test-admin", password="test-password")
        response = self.client.get(self.pin_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "mboard/post_pin.html")

    def test_moderator_can_access_pin_page(self):
        self.client.login(username="test-moderator", password="test-password")
        response = self.client.get(self.pin_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "mboard/post_pin.html")

    def test_regular_user_cannot_access_pin_page(self):
        self.client.login(username="test-user", password="test-password")
        response = self.client.get(self.pin_url)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith(reverse("login")))

    def test_banned_user_cannot_access_pin_page(self):
        # note: no need to test for banned admins or mods: status is `one of`.
        self.client.login(username="test-banned", password="test-password")
        response = self.client.get(self.pin_url)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith(reverse("login")))

    def test_admin_can_pin_post(self):
        self.client.login(username="test-admin", password="test-password")
        response = self.client.post(self.pin_url)
        self.assertEqual(response.status_code, 302)
        self.post.refresh_from_db()
        self.assertTrue(self.post.pinned)

    def test_moderator_can_pin_post(self):
        self.client.login(username="test-moderator", password="test-password")
        response = self.client.post(self.pin_url)
        self.assertEqual(response.status_code, 302)
        self.post.refresh_from_db()
        self.assertTrue(self.post.pinned)

    def test_regular_user_cannot_pin_post(self):
        self.client.login(username="test-user", password="test-password")
        response = self.client.post(self.pin_url)
        self.assertEqual(response.status_code, 302)
        self.post.refresh_from_db()
        self.assertFalse(self.post.pinned)

    def test_banned_user_cannot_pin_post(self):
        self.client.login(username="test-banned", password="test-password")
        response = self.client.post(self.pin_url)
        self.assertEqual(response.status_code, 302)
        self.post.refresh_from_db()
        self.assertFalse(self.post.pinned)
        self.client.logout()

    def test_pin_unpin_toggle(self):
        self.client.login(username="test-admin", password="test-password")

        # Pin the post
        self.client.post(self.pin_url)
        self.post.refresh_from_db()
        self.assertTrue(self.post.pinned)

        # Unpin the post
        self.client.post(self.pin_url)
        self.post.refresh_from_db()
        self.assertFalse(self.post.pinned)

    def test_pinned_posts_appear_first(self):
        unpinned_post = Post.objects.create(
            title="Unpinned Post", url="https://example.com/unpinned", user=self.regular_user
        )
        self.client.login(username="test-admin", password="test-password")
        self.client.post(self.pin_url)
        response = self.client.get(reverse("mboard:index"))
        posts = response.context["page_obj"]
        self.assertEqual(posts[0].id, self.post.id)
        self.assertTrue(posts[0].pinned)
        unpinned_posts = [p for p in posts if not p.pinned]
        self.assertIn(unpinned_post, unpinned_posts)

    def test_pin_nonexistent_post(self):
        self.client.login(username="test-admin", password="test-password")
        non_existent_pin_url = reverse("mboard:post_pin", args=[99999])
        response = self.client.post(non_existent_pin_url)
        self.assertEqual(response.status_code, 404)


class CommentDetailTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="test-user", password="test-password")
        self.post = Post.objects.create(title="Test Post", url="https://example.com", user=self.user)
        self.top_comment = Comment.objects.create(
            content="Top level comment", user=self.user, post=self.post, parent=None
        )

    def test_detail_view_returns_200(self):
        url = reverse("mboard:comment_detail", args=[self.top_comment.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_detail_view_404_for_invalid_comment(self):
        url = reverse("mboard:comment_detail", args=[666])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_nested_replies_are_included(self):
        reply1 = Comment.objects.create(content="First reply", user=self.user, post=self.post, parent=self.top_comment)
        reply2 = Comment.objects.create(content="Reply to reply", user=self.user, post=self.post, parent=reply1)

        url = reverse("mboard:comment_detail", args=[self.top_comment.id])
        response = self.client.get(url)

        self.assertContains(response, "Top level comment")
        self.assertContains(response, "First reply")
        self.assertContains(response, "Reply to reply")

    def test_max_depth_nesting(self):
        current_comment = self.top_comment
        for i in range(MAX_DEPTH + 1):
            current_comment = Comment.objects.create(
                content=f"Nested reply level {i + 1}", user=self.user, post=self.post, parent=current_comment
            )

        url = reverse("mboard:comment_detail", args=[self.top_comment.id])
        response = self.client.get(url)

        for i in range(MAX_DEPTH):
            self.assertContains(response, f"Nested reply level {i + 1}")
        self.assertNotContains(response, f"Nested reply level {MAX_DEPTH + 1}")
        self.assertContains(response, "more replies...")

    def test_detail_view_shows_post_context(self):
        url = reverse("mboard:comment_detail", args=[self.top_comment.id])
        response = self.client.get(url)
        self.assertEqual(response.context["post"], self.post)

    def test_fan_status_for_authenticated_user(self):
        self.client.login(username="test-user", password="test-password")
        self.top_comment.fans.add(self.user)

        url = reverse("mboard:comment_detail", args=[self.top_comment.id])
        response = self.client.get(url)

        comment_in_context = response.context["comments"][0]
        self.assertTrue(hasattr(comment_in_context, "is_fan"))
        self.assertTrue(comment_in_context.is_fan)

    def test_ordering_of_nested_comments(self):
        reply1 = Comment.objects.create(
            content="Older reply",
            user=self.user,
            post=self.post,
            parent=self.top_comment,
        )
        reply2 = Comment.objects.create(
            content="Newer reply",
            user=self.user,
            post=self.post,
            parent=self.top_comment,
        )

        url = reverse("mboard:comment_detail", args=[self.top_comment.id])
        response = self.client.get(url)
        content = response.content.decode()
        newer_position = content.find("Newer reply")
        older_position = content.find("Older reply")
        self.assertLess(newer_position, older_position)
