from random import choice
from random import randint

from django.contrib.auth import get_user_model
from faker import Faker

from app.models import Board
from app.models import Comment
from app.models import Keyword
from app.models import Post

User = get_user_model()


def generate_user() -> User:
    fake = Faker()
    user = User(username=fake.user_name())
    user.set_password(fake.password())
    return user


POST_LEN = (3, 8)


def random_user():
    assert User.objects.exists()
    return User.objects.order_by("?").first()


def random_board():
    assert Board.objects.exists()
    return choice([None, Board.objects.order_by("?").first()])


def random_keywords():
    assert Keyword.objects.exists()
    keywords = list(Keyword.objects.all())  # Get all keywords first
    k = randint(0, len(keywords))  # Get random number of keywords to select
    return Keyword.objects.order_by("?")[:k]  # Return random selection


def generate_post(author: User | None = None) -> Post:
    fake = Faker()
    post = Post(
        url=fake.url(),
        title=fake.sentence(
            nb_words=randint(*POST_LEN),
            variable_nb_words=True,
        ),
        user=author if author is not None else random_user(),
        board=random_board(),
    )
    post.save()
    post.keywords.set(random_keywords())
    return post


COMMENT_LEN = (1, 5)


def random_post():
    assert Post.objects.exists()
    return Post.objects.order_by("?").first()


def random_comment(post: Post):
    if not post.comments.exists() or not randint(0, 4):
        return post
    return post.comments.order_by("?").first()


def generate_comment(author: User | None = None, parent: Post | Comment | None = None) -> Comment:
    if parent is None:
        parent = random_comment(random_post())

    fake = Faker()
    comment = Comment(
        content=fake.paragraph(nb_sentences=randint(*COMMENT_LEN)),
        user=author if author is not None else random_user(),
        post=parent if isinstance(parent, Post) else parent.post,
        parent=None if isinstance(parent, Post) else parent,
    )
    return comment
