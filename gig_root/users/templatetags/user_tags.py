import calendar

from django.utils import timezone
from django import template

register = template.Library()


def remove(match=None, arg=None):
    """
    helper function that removes from arg the `match` part.
    """
    if arg is None or match is None:
        return ""
    elif match in arg:
        return arg.replace(match,'')
    else:
        return arg

@register.filter(name='remove_meta')
def remove_meta(arg=None):
    """
    filter function that removes substring `__all__` from `arg`
    """
    return remove(match='__all__',arg=arg)


@register.filter(name='add_attr')
def add_attr(field, css):
    """
    filter function that adds a particular string to class of an html element.
    Useful to add dynamically bootstrap classes
    """
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
    """
    Filter function that adds 0 to time. e.g. correct time 4:3 to 04:03.
    """
    str_h= '0' + str(hour) if hour < 10 else str(hour)
    str_min= '0' + str(minute) if minute < 10 else str(minute)

    return str_h + ':' + str_min

@register.filter(name='fancy_date')
def fancy_date(event_date_time):
    """
    Filter function that display date as `Today`, `Tomorrow`,..., when possible.
    """
    today=timezone.now().date()
    event_date=event_date_time.date()

    if today == event_date:
        return "Today at " + correct_time(event_date_time.hour, event_date_time.minute)
    elif today  + timezone.timedelta(days=1) == event_date:
        return "Tomorrow at " + correct_time(event_date_time.hour, event_date_time.minute)
    elif today  > event_date:
        dt =str(event_date.day)+ "/"+ str(event_date.month)+"/"+str(event_date.year) +" at " + correct_time(event_date_time.hour, event_date_time.minute)
        return "Already played ("+ dt+ ")"
    else:
        return calendar.month_name[event_date.month] +" "+ str(event_date.day)+ " at " + correct_time(event_date_time.hour, event_date_time.minute)
