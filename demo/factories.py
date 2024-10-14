from random import randint

from django.contrib.auth import get_user_model
from app.models import Post, Comment

from faker import Faker

User = get_user_model()


def generate_user() -> User:
    fake = Faker()
    user = User(username=fake.user_name())
    user.set_password(fake.password())
    return user


POST_LEN = (4, 10)


def random_user():
    assert User.objects.exists()
    return User.objects.order_by('?').first()


def generate_post(author: User | None = None) -> Post:
    fake = Faker()
    post = Post(
        url=fake.url(),
        title=fake.sentence(
            nb_words=randint(*POST_LEN),
            variable_nb_words=True,
        ),
        user=author if author is not None else random_user(),
    )
    return post


COMMENT_LEN = (1, 5)


def random_post():
    assert Post.objects.exists()
    return Post.objects.order_by('?').first()


def random_comment(post: Post):
    if not post.comments.exists() or not randint(0, 3):
        return post
    return post.comments.order_by('?').first()


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
