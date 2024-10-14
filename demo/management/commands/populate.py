from random import random

from django.core.management.base import BaseCommand

from app.models import Post
from demo.factories import generate_comment
from demo.factories import generate_post
from demo.factories import generate_user

NUM_USERS = 50
NUM_POSTS = 100
NUM_COMMS = 1000


class Command(BaseCommand):
    help = "Populate the database with users, posts, and comments"

    def handle(self, *args, **kwargs):
        print(f"Creating {NUM_USERS} fake users..")
        for _ in range(NUM_USERS):
            generate_user().save()

        print(f"Creating {NUM_POSTS} fake posts..")
        for _ in range(NUM_POSTS):
            generate_post().save()

        print(f"Creating {NUM_COMMS} fake comments..")
        for _ in range(NUM_COMMS):
            generate_comment().save()

        print("Done.")
