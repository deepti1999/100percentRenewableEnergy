from django import template

register = template.Library()

@register.filter
def split_count(value, delimiter):
    """Return the number of parts when splitting a string"""
    if not value:
        return 0
    return len(str(value).split(delimiter))