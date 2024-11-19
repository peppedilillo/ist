from urllib.parse import urlparse

from django.core.exceptions import ValidationError
from django.core.validators import URLValidator
from django.forms import ModelForm
from django.forms import Textarea

from .models import Board
from .models import Comment
from .models import Keyword
from .models import Post


class PostForm(ModelForm):
    class Meta:
        model = Post
        fields = ["title", "url", "board", "keywords"]

    def clean_url(self):
        validate = URLValidator()
        url = self.cleaned_data.get("url")

        parsed = urlparse(url)
        if not parsed.scheme:
            url = f"https://{url}"

        try:
            validate(url)
        except ValidationError:
            raise ValidationError("URL is not valid.")

        return url


class PostEditForm(ModelForm):
    class Meta:
        model = Post
        # we do not allow url to be edited to avoid rickrolls
        fields = ["title"]


class CommentForm(ModelForm):
    class Meta:
        model = Comment
        fields = ["content"]
        widgets = {
            "content": Textarea(attrs={"rows": 6}),
        }
