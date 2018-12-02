from django.shortcuts import render
from django.http import HttpResponse
from django.urls import reverse

from . import search

def home(request):
    """
    The home page of gigForMusicians.
    The home page focus on displaying several kinds of upcoming events.
    Depending whether the user is logged in or not.
    """

    user=request.user
    has_artistProfile=user.has_artistProfile() if user.is_authenticated else False
    upc_evs=search.get_upcoming_events()
    foll_b_evs= search.get_follow_bands_events(user) if user.is_authenticated else False
    part_evs= search.get_participate_events(user) if user.is_authenticated else False
    might_like_evs= search.get_might_like_events(user) if user.is_authenticated else False

    context= {
        'user': user,
        'has_artistProfile': has_artistProfile,
        'upcoming_events': upc_evs,
        'follow_band_events': foll_b_evs,
        'participate_events': part_evs,
        'might_like_events': might_like_evs,
    }
    return render(request, "gig/home.html", context=context)
