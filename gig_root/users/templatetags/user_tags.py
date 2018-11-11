
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


@register.filter(name='add_attr')
def add_attr(field, css):
    attrs = {}
    definition = css.split(',')

    for d in definition:
        if ':' not in d:
            attrs['class'] = d
        else:
            key, val = d.split(':')
            attrs[key] = val

    return field.as_widget(attrs=attrs)
