from random import random

from django.core.management.base import BaseCommand

from demo.factories import generate_comment
from demo.factories import generate_post
from demo.factories import generate_user


class Command(BaseCommand):
    help = "Populate the database with users, posts, and comments"

    def add_arguments(self, parser):
        parser.add_argument(
            "--users", type=int, default=10, help="Number of users to create"
        )
        parser.add_argument(
            "--posts", type=int, default=100, help="Number of posts to create"
        )
        parser.add_argument(
            "--comments", type=int, default=1000, help="Number of comments to create"
        )

    def handle(self, *args, **options):
        num_users = options["users"]
        num_posts = options["posts"]
        num_comments = options["comments"]

        print(f"Creating {num_users} fake users..")
        for _ in range(num_users):
            generate_user().save()

        print(f"Creating {num_posts} fake posts..")
        for _ in range(num_posts):
            generate_post().save()

        print(f"Creating {num_comments} fake comments..")
        for _ in range(num_comments):
            generate_comment().save()

        print("Done.")
