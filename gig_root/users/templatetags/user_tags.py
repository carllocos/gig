
from django import template

register = template.Library()


def remove(match=None, arg=None):
    if arg is None or match is None:
        return ""
    elif match in arg:
        return arg.replace(match,'')
    else:
        return arg

@register.filter(name='remove_meta')
def remove_meta(arg=None):
    return remove(match='__all__',arg=arg)
