from urllib.parse import urlparse

from django import template
from django.utils.timesince import timesince
import mistune

register = template.Library()

colors = {
    "all": "red-light",
    "news": "green-light",
    "papers": "yellow-light",
    "code": "blue-light",
    "jobs": "magenta-light",
}


@register.filter
def board_color(header_text):
    """Associates a color to each of the messageboard board.
    Note that these colors should also be safelisted in the tailwind config,
    otherwise tailwind may never now of them."""
    return colors.get(header_text, "base-100")


@register.filter
def truncatesmart(value, limit=24):
    """
    Truncates a URL's domain+path after a given number of chars keeping whole words.
    Uses urlparse for safe URL handling.
    """
    try:
        limit = int(limit)
    except ValueError:
        return value

    parsed = urlparse(value)
    # Get domain and path, ignore scheme
    display_url = parsed.netloc + parsed.path

    if len(display_url) <= limit:
        return display_url
    return display_url.split("/", 1)[0] + "/.."


@register.filter
def timeago(value):
    return timesince(value, depth=1)


@register.filter
def addclass(value, arg):
    return value.as_widget(attrs={"class": arg})


_markdown = mistune.create_markdown(
    escape=True,
    plugins=[
        "url",
        "strikethrough",
        "footnotes",
        "table",
    ],
)


@register.filter
def markdown(value: str):
    return _markdown(value)
