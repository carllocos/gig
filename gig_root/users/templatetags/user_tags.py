import datetime

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


@register.filter(name='correct_time')
def correct_time(hour, minute):
    str_h= '0' + str(hour) if hour < 10 else str(hour)
    str_min= '0' + str(minute) if minute < 10 else str(minute)

    return str_h + ':' + str_min

@register.filter(name='fancy_date')
def fancy_date(event_date_time):
    today=datetime.date.today()
    event_date=event_date_time.date()

    if today == event_date:
        return "Today at " + str(event_date_time.hour) + ":" + str(event_date_time.minute)
    elif today  + datetime.timedelta(days=1) == event_date:
        return "Tomorrow at " + str(event_date_time.hour) + ":" + str(event_date_time.minute)
    elif today  > event_date:
        return "Already played"
    else:
        return event_date_time
