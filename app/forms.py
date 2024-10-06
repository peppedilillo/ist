from django.forms import ModelForm
from django.core.exceptions import ValidationError
from django.core.validators import URLValidator

from .models import Post, Comment


class PostForm(ModelForm):
    class Meta:
        model = Post
        fields = ["title", "url"]

    def clean_url(self):
        validate = URLValidator()
        url = self.cleaned_data.get('url')

        if not url.startswith(('http://', 'https://')):
            url = f"https://{url}"

        try:
            validate(url)
        except ValidationError:
            raise ValidationError("URL is not valid.")

        return url


class CommentForm(ModelForm):
    class Meta:
        model = Comment
        fields = ["content"]