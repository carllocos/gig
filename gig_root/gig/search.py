from django.utils import timezone

from events.models import Event
from musicians.models import Band


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
