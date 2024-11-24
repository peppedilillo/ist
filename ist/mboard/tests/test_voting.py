from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta

from ..models import Post, Comment, save_new_comment, save_new_post
from ..scores import compute_score, arbitrary_date


class VotingSystemTests(TestCase):
    def setUp(self):
        self.author = get_user_model().objects.create_user(
            username="test-author",
            password="test-password"
        )
        self.voter = get_user_model().objects.create_user(
            username="test-voter",
            password="test-password"
        )
        self.banned = get_user_model().objects.create_user(
            username="test-banned",
            password="test-password",
            status="b"
        )

        self.post = save_new_post(
            title="Test Post",
            author=self.author,
            url="https://example.com",
            board=None,
        )

        self.comment = save_new_comment(
            content="Test Comment",
            author=self.author,
            post=self.post,
            parent=None
        )

        self.post_upvote_url = reverse('mboard:post_upvote', args=[self.post.id])
        self.comment_upvote_url = reverse('mboard:comment_upvote', args=[self.comment.id])
        self.initial_post_score = compute_score(1, self.post.date)

    def test_post_initial_state(self):
        """Post should start with author's automatic upvote"""
        self.assertEqual(self.post.nlikes, 1)
        self.assertTrue(self.post.fans.filter(id=self.author.id).exists())
        self.assertEqual(self.post.score, self.initial_post_score)

    def test_post_upvote_authentication_required(self):
        response = self.client.post(self.post_upvote_url)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertFalse(data['success'])

    def test_post_upvote_banned_user(self):
        self.client.login(username="test-banned", password="test-password")
        response = self.client.post(self.post_upvote_url)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertFalse(data['success'])

    def test_successful_post_upvote(self):
        self.client.login(username="test-voter", password="test-password")
        response = self.client.post(self.post_upvote_url)
        data = response.json()

        self.assertEqual(response.status_code, 200)
        self.assertTrue(data['success'])
        self.assertEqual(data['nlikes'], 2)
        self.assertTrue(data['isupvote'])

        self.post.refresh_from_db()
        self.assertEqual(self.post.nlikes, 2)
        self.assertTrue(self.post.fans.filter(id=self.voter.id).exists())

        expected_score = compute_score(2, self.post.date)
        self.assertEqual(round(self.post.score, 5), round(expected_score, 5))

    def test_post_upvote_toggle(self):
        self.client.login(username="test-voter", password="test-password")

        # posting first upvotes
        response = self.client.post(self.post_upvote_url)
        data = response.json()
        self.post.refresh_from_db()
        self.assertEqual(self.post.nlikes, 2)
        self.assertTrue(data['isupvote'])
        self.assertTrue(self.post.fans.filter(id=self.voter.id).exists())

        # posting a second time removes like
        response = self.client.post(self.post_upvote_url)
        data = response.json()
        self.post.refresh_from_db()
        self.assertEqual(self.post.nlikes, 1)
        self.assertFalse(data['isupvote'])
        self.assertFalse(self.post.fans.filter(id=self.voter.id).exists())

    def test_comment_upvote_system(self):
        self.client.login(username="test-voter", password="test-password")

        self.assertEqual(self.comment.nlikes, 1)

        response = self.client.post(self.comment_upvote_url)
        data = response.json()
        self.comment.refresh_from_db()

        self.assertTrue(data['success'])
        self.assertEqual(self.comment.nlikes, 2)
        self.assertTrue(self.comment.fans.filter(id=self.voter.id).exists())

    def test_comment_upvote_toggle(self):
        self.client.login(username="test-voter", password="test-password")

        # posting first upvotes
        response = self.client.post(self.comment_upvote_url)
        data = response.json()
        self.comment.refresh_from_db()
        self.assertEqual(self.comment.nlikes, 2)
        self.assertTrue(data['isupvote'])
        self.assertTrue(self.comment.fans.filter(id=self.voter.id).exists())

        # posting a second time removes like
        response = self.client.post(self.comment_upvote_url)
        data = response.json()
        self.comment.refresh_from_db()
        self.assertEqual(self.comment.nlikes, 1)
        self.assertFalse(data['isupvote'])
        self.assertFalse(self.comment.fans.filter(id=self.voter.id).exists())

    def test_upvote_nonexistent_content(self):
        self.client.login(username="test-voter", password="test-password")

        # Try to upvote non-existent post
        response = self.client.post(reverse('mboard:post_upvote', args=[99999]))
        self.assertEqual(response.status_code, 404)

        # Try to upvote non-existent comment
        response = self.client.post(reverse('mboard:comment_upvote', args=[99999]))
        self.assertEqual(response.status_code, 404)

    def test_score_decay_over_time(self):
        """Test that post scores properly decay over time"""
        now = timezone.now()

        old_post = save_new_post(
            title="Old Post",
            url="https://example.com/old",
            author=self.author,
            board=None,
        )
        old_post.date = now - timedelta(days=7)
        old_post.save()
        new_post = save_new_post(
            title="New Post",
            url="https://example.com/new",
            author=self.author,
            board=None,
        )

        # Give both posts same number of likes
        self.client.login(username="test-voter", password="test-password")
        self.client.post(reverse('mboard:post_upvote', args=[old_post.id]))
        self.client.post(reverse('mboard:post_upvote', args=[new_post.id]))

        old_post.refresh_from_db()
        new_post.refresh_from_db()

        # New post should have higher score despite same likes
        self.assertEqual(old_post.nlikes, new_post.nlikes)
        self.assertGreater(new_post.score, old_post.score)


class VotingFrontendTests(TestCase):
    def setUp(self):
        self.author = get_user_model().objects.create_user(
            username="test-author",
            password="test-password"
        )
        self.voter = get_user_model().objects.create_user(
            username="test-voter",
            password="test-password"
        )
        self.post = Post.objects.create(
            title="Test Post",
            url="https://example.com",
            user=self.author
        )
        self.comment = Comment.objects.create(
            content="Test Comment",
            post=self.post,
            user=self.author
        )

    def test_post_upvote_ui_elements(self):
        """Test that upvote UI elements are correctly rendered"""
        self.client.login(username="test-voter", password="test-password")
        response = self.client.get(reverse('mboard:post_detail', args=[self.post.id]))

        # Check for upvote button
        self.assertContains(response, f'id="up_{self.post.id}"')
        self.assertContains(response, 'data-state="inactive"')
        self.assertContains(response, '🔥')  # Fire emoji

        # Check score display
        self.assertContains(response, f'id="score_{self.post.id}"')
        self.assertContains(response, f"{self.post.nlikes} point")

    def test_upvoted_post_ui(self):
        """Test UI representation of an upvoted post"""
        self.client.login(username="test-voter", password="test-password")

        # Upvote the post
        self.client.post(reverse('mboard:post_upvote', args=[self.post.id]))

        response = self.client.get(reverse('mboard:post_detail', args=[self.post.id]))

        # Active upvote icon should be visible
        self.assertContains(response, 'data-state="active"')
        self.assertContains(response, 'grayscale-0 opacity-100')

        # Inactive icon should be hidden
        self.assertContains(response, 'grayscale opacity-30')
        self.assertContains(response, 'hidden')

    def test_unauthenticated_user_ui(self):
        """Test that unauthenticated users see appropriate UI"""
        response = self.client.get(reverse('mboard:post_detail', args=[self.post.id]))

        # Should not see upvote buttons
        self.assertNotContains(response, 'onclick="upvotePost')
        self.assertNotContains(response, 'onclick="upvoteComment')

        # Should still see scores
        self.assertContains(response, f"{self.post.nlikes} point")
        self.assertContains(response, f"{self.comment.nlikes} point")

    def test_vote_redirection_link(self):
        """Test that upvote attempts by anonymous users have correct redirect URL"""
        response = self.client.get(reverse('mboard:post_detail', args=[self.post.id]))
        # Check for login redirect URL in data attribute
        self.assertContains(response, f'redirect="{reverse("login")}"')
