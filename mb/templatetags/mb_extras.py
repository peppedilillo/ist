from django import template
from django.utils.timesince import timesince

from urllib.parse import urlparse


register = template.Library()


@register.filter
def board_color(header_text):
    """Associates a color to each of the messageboard board. 
    Note that these colors should also be safelisted in the tailwind config,
    otherwise tailwind may never now of them."""
    colors = {
        'news': 'text-red-light',
        'papers': 'text-yellow-light',
        'code': 'text-blue-light',
        'jobs': 'text-magenta-light'
    }
    return colors.get(header_text, 'text-base-300')


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
    return display_url.split('/', 1)[0] + '/..'


@register.filter
def timeago(value):
    return timesince(value, depth=1)


@register.filter(name='addclass')
def addclass(value, arg):
    return value.as_widget(attrs={'class': arg})
