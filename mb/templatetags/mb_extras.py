from django import template

register = template.Library()

@register.filter
def board_color(header_text):
    colors = {
        'news': 'text-red-light',
        'papers': 'text-yellow-light',
        'code': 'text-blue-light',
        'jobs': 'text-magenta-light'
    }
    return colors.get(header_text, 'text-base-300')