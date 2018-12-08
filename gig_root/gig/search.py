import operator
from functools import reduce

from django.utils import timezone
from django.db.models import Q
from events.models import Event
from musicians.models import Band
from django.shortcuts import reverse


def get_suggestions(query):
    """
    function that return a dictionary containing a list of bands and events that matches `query`.
    """
    band_filter_condition = reduce(operator.or_, [Q(name__icontains=query), Q(_genres__icontains=query)])

    bands=[__band_to_dict(band) for band in Band.objects.filter(band_filter_condition)]
    events=[__event_to_dict(event) for event in Event.objects.filter(name__icontains=query)]

    return {'bands': bands, 'events': events}

def get_upcoming_events():
    """
    `get_upcoming_events` returns a queryset of all events that will soon take place.
    """
    return Event.get_upcoming_events()

def get_follow_bands_events(user):
    """
    `get_follow_bands_events` returns a queryset of upcoming events created by bands that the user follows.
    """
    events= Event.objects.none()
    for follows in user.follow_set.all():
        events = events.union(follows.band.get_upcoming_events())

    return events.order_by('date')


def get_participate_events(user):
    """
    `get_participate_events` returns a queryset of all events for which the user said he/she would participate
    """
    now=timezone.now()
    evs_lst= []
    par_qs=user.participant_set.filter(event__date__gte=now).order_by('event__date').select_related('event')
    for par_ins in par_qs:
        evs_lst.append(par_ins.event)
    return evs_lst

def get_might_like_events(user):
    """
    `get_might_like_events` returns a queryset of all events that the user might like
    """
    bands=get_bands_might_like(user)
    events= Event.objects.none()
    for b in bands:
        events = events.union(b.get_upcoming_events())

    return events.order_by('date')


def get_bands_might_like(user):
    """
    `get_bands_might_like` returns a queryset of all bands that the user might like
    """
    upvotes = user.bandprofilevote_set.filter(is_upvote=True).select_related('band')
    follows_bands = set(f.band for f in user.follow_set.all())
    liked_bands = set(vote.band for vote in upvotes) | follows_bands
    if not liked_bands:
        return []

    genres=__band_genres(liked_bands)
    owns_bands= user.artistmodel.owns.all() if user.artistmodel else []
    for b in owns_bands:
        follows_bands.add(b)
    similar_bands= __search_similar_bands(genres, exclude_bands=follows_bands)

    return similar_bands

def __search_similar_bands(genres,exclude_bands=None):
    if exclude_bands is None:
        exclude_bands=[]

    rst=[]
    for b in Band.objects.all():
        if b in exclude_bands:
            continue
        for g in genres:
            if g.lower() in genres:
                rst.append(b)
                break
    return rst

def __band_genres(bands):
    set_genres= set()
    for b in bands:
        for g in b.genres:
            set_genres.add(g.lower())

    return set_genres


def __band_to_dict(band):
    """
    helper function that transform a band instance into a dictionary
    """
    return {
        'name': band.name,
        'id': band.pk,
        'pic_id': band.profile_pic.public_id,
        'url': reverse("musicians:band-profile", kwargs={'profile_id': band.pk}),
    }

def __event_to_dict(event):
    """
    helper function that transform an event instance into a dictionary
    """
    return {
            'name': event.name,
            'id': event.pk,
            'pic_id': event.picture.public_id,
            'url': reverse("events:profile", kwargs={'event_id': event.pk}),
            }
