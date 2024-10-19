import re

from django.core.exceptions import ValidationError
from django.core.validators import URLValidator
from django.forms import ModelForm
from django.forms import Textarea

from .models import Comment
from .models import Post
from .settings import BOARDS, BOARDS_PREFIXES, BOARD_PREFIX_SEPARATOR


class PostForm(ModelForm):
    class Meta:
        model = Post
        fields = ["title", "url", "board"]

    def clean_url(self):
        validate = URLValidator()
        url = self.cleaned_data.get("url")

        if not url.startswith(("http://", "https://")):
            url = f"https://{url}"

        try:
            validate(url)
        except ValidationError:
            raise ValidationError("URL is not valid.")

        return url

    def clean(self):
        """
        Cleans up the title and checks if the user is adding a prefix to address
        a specific board.
        """
        cleaned_data = super().clean()
        title = cleaned_data["title"]
        for board_id, board_prefix in BOARDS_PREFIXES.items():
            pattern = rf"(?i)\b{board_prefix}s?\b\s*{BOARD_PREFIX_SEPARATOR}+"
            if re.match(pattern, title):
                cleaned_data["title"] = f"{board_prefix}{BOARD_PREFIX_SEPARATOR} {title.split(':', 1)[1].strip()}"
                cleaned_data["board"] = board_id
                return cleaned_data
        self.cleaned_data["board"] = None
        return cleaned_data


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
            "content": Textarea(attrs={"rows": 6, "cols": 60}),
        }
