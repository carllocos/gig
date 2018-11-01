from django.http import HttpResponse , JsonResponse
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods

from .forms import CreateArtistForm
from .models import ArtistModel
from .artist_util import has_not_artist_profile, suggest_genres, suggest_instruments


def home(request):
    return HttpResponse("This is home of artists")



def view_profile(request, profile_id):
    """
    The view that renders an artist profile based on a `profile_id`.
    If the requester is the owner of the profile, another kind of template
    is rendered.
    """

    artist = ArtistModel.get_artist(profile_id)

    if not artist:
        context= {'short_message': "The request artist profile does not exists.",
                  'title_msg': "Profile does not exists",
                  'titple_page': "Bad request"}
        return render(request, '/users/short_message.html',context=context)

    #Here we are certain that ArtistModel with private key `profile_id` exists
    user= request.user

    #is_owner tells wheter the user accessing artist profile with id `profile_id` is the owner of that profile
    is_owner = user.is_authenticated and user.has_artistProfile() and user.get_artist().pk == profile_id

    context={'user': user,
             'artist': artist,
             'is_owner': is_owner,
             'profile_pic_id': artist.get_profile_pic_id(),
             'bg_pic_id': artist.get_background_pic_id()}

    return render(request, 'artists/profile.html', context=context)

@has_not_artist_profile
@require_http_methods(["GET", "POST"])
@login_required
def register_artist_view(request):
    """
    The view called when a user wants to register an ArtistProfile.
    """

    if request.method =="GET":
        form = CreateArtistForm()
        return render(request, "artists/register_profile.html", {'form': form, 'user': request.user})

    else:
        art_form = CreateArtistForm(request.POST, request.FILES)

        if art_form.is_valid(request.POST):
            art=art_form.save(request.user)
            return redirect('artists:artist-profile', profile_id=art.pk)
        else:
            return render(request, 'users/social_account_form.html', {'form': form})

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
