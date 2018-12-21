from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.urls import reverse
from django.views.decorators.http import require_http_methods

from users.util import getHTTP_Protocol
from . import search as dbSearch

def home(request):
    """
    The home page of gigForMusicians, focus on displaying upcoming events.
    """

    user=request.user
    has_artistProfile=user.has_artistProfile() if user.is_authenticated else False
    upc_evs=dbSearch.get_upcoming_events()
    random_bands= dbSearch.get_randomBands(amount=1)

    context= {
        'user': user,
        'has_artistProfile': has_artistProfile,
        'upcoming_events': upc_evs,
        'random_bands': random_bands,
        'http_protocol': getHTTP_Protocol()
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
