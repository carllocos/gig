from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.urls import reverse
from django.views.decorators.http import require_http_methods

from . import search as dbSearch

def home(request):
    """
    The home page of gigForMusicians.
    The home page focus on displaying several kinds of upcoming events.
    Depending whether the user is logged in or not.
    """

    user=request.user
    has_artistProfile=user.has_artistProfile() if user.is_authenticated else False
    upc_evs=dbSearch.get_upcoming_events()
    foll_b_evs= dbSearch.get_follow_bands_events(user) if user.is_authenticated else False
    part_evs= dbSearch.get_participate_events(user) if user.is_authenticated else False
    might_like_evs= dbSearch.get_might_like_events(user) if user.is_authenticated else False

    random_bands= dbSearch.get_randomBands()
    
    context= {
        'user': user,
        'has_artistProfile': has_artistProfile,
        'upcoming_events': upc_evs,
        'follow_band_events': foll_b_evs,
        'participate_events': part_evs,
        'might_like_events': might_like_evs,
        'random_bands': random_bands,
    }
    return render(request, "gig/home.html", context=context)


@require_http_methods(["GET"])
def search_query(request):
    query= request.GET.get('query', '')
    context={ 'query': query}

    matches= {'bands': [], 'events': []} if query == '' else dbSearch.search_query(query)
    context.update(matches)
    return render(request, "gig/search_results.html", context=context)

@require_http_methods(["GET"])
def search_suggestions(request):
    query = request.GET.get("query")
    results=dbSearch.get_suggestions(query)
    return JsonResponse(results)
