from django.http import HttpResponse , JsonResponse
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.views.generic import FormView
from django.views.decorators.http import require_http_methods

from .forms import CreateArtistForm


def home(request):
    return HttpResponse("This is home of artists")

@require_http_methods(["GET", "POST"])
@login_required #find out how to come back here after login
def register_artist_view(request):
    if request.method =="GET":
        user= request.user
        initial_data= {
            'first_name': user.first_name, 'last_name': user.last_name
        }
        form = CreateArtistForm(initial=initial_data)

        return render(request, "artists/register_profile.html", {'form': form, 'user': request.user})

    else:
        form = CreateArtistForm(request.POST)
        if form.is_valid(request.POST):
            form.save(request.user)
            return HttpResponse("form valid")
        else:
            return render(request, 'users/social_account_form.html', {'form': form})

from artists.artist_util import suggest_genres, suggest_instruments

@require_http_methods(["GET"])
@login_required
def ajax_suggestions(request):
    if not request.is_ajax():
        return JsonResponse({'suggestions': False})

    if request.GET.get('kind', False) == 'genre':
        suggestions = suggest_genres(request.GET.get('value', ''))
        return JsonResponse({'suggestions': suggestions})

    elif request.GET.get('kind', False) == 'instrument':
        suggestions = suggest_instruments(request.GET.get('value', ''))
        return JsonResponse({'suggestions': suggestions})

    return JsonResponse({'suggestions': False})
