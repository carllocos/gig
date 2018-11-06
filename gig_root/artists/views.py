from django.http import HttpResponse , JsonResponse
from django.shortcuts import render, redirect, reverse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods

from .forms import CreateArtistForm
from .models import ArtistModel
from .artist_util import has_not_artist_profile, suggest_genres, suggest_instruments, has_artist_profile


def home(request):
    return HttpResponse("This is home of artists")

def no_profile(request):
    """
    no_profile view is meant to display a message to users that try to perform operations only meant
    for users with an aritstprofile. The response invites the users to register their artist profile.
    """
    context= {'short_message': "You are trying to perform an action that requires you to dispose of an artist profile. To register your artist profile click on the following link",
              'title_msg': "Create your artist profile",
              'titple_page': "Bad request",
              'link': reverse('artists:register')}
    return render(request, 'users/short_message.html', context=context)

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
                  'title_page': "Bad request"}
        return render(request, 'users/short_message.html',context=context)

    #Here we are certain that ArtistModel with private key `profile_id` exists
    user= request.user

    #is_owner tells wheter the user accessing artist profile with id `profile_id` is the owner of that profile
    is_owner = user.is_authenticated and user.has_artistProfile() and user.get_artist().pk == profile_id
    linups= artist.get_active_bands()

    context={'user': user,
             'artist': artist,
             'is_owner': is_owner,
             'profile_pic_id': artist.get_profile_pic_id(),
             'bg_pic_id': artist.get_background_pic_id(),
             'linups': linups,
             }

    return render(request, 'artists/profile.html', context=context)

@require_http_methods(["GET", "POST"])
@login_required
@has_not_artist_profile
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

@require_http_methods(['POST'])
@login_required
def direct_upload_complete(request):
    return JsonResponse({'response': 'Got it'})


#TODO Validation of post input.
@require_http_methods(['POST'])
@login_required
@has_artist_profile
def update_genre_idol_instrument(request):
    """
    Ajax update for genres, instruments or idols of an artist profile. The POST request must contain 3 differents keys;
    1. 'to_update', which specifies what will be updated e.g. `instrument`, `genre` or `idol`
    2. 'operation', which specifies what type of operation will be performed `remove` or `add`
    3. 'val', which specifies the value to be removed or added

    e.g. of a received json
    {
        'to_update': 'genre',
        'operation': 'remove',
        'val': 'Rock'
    }

    This function returns three different keys.
    1. 'is_executed': a boolean that tells whether the requested operation was succesful.
    2. 'val': the value involved in the operation
    3. 'reason': a reason for why a request might have fail. Is empty when 'is_executed' is True
    {
        'is_executed': True,
        'val': value
    }
    """
    if not request.is_ajax():
        return JsonResponse({'is_executed': False, 'reason': 'request is not ajax'})

    operation = request.POST.get('operation', '')
    if operation != 'remove' and operation!= 'add':
        return JsonResponse({'is_executed': False, 'reason': f'operation is not remove or add. Given {operation}'})

    to_update = request.POST.get('to_update', '')
    if to_update !='instrument' and to_update != 'genre' and to_update !='idol':
        return JsonResponse({'is_executed': False, 'reason': 'update type is wrong'})

    val = request.POST.get('val', False)
    if not val or val =='':
        return JsonResponse({'is_executed': False, 'reason': 'no value was specified'})

    art=request.user.get_artist()
    reason=''
    if operation == 'add':
        if to_update == 'instrument':
            succes=art.add_instrument(val)
            if not succes:
                reason=f"{val} is already saved as instrument"
        elif to_update == 'genre':
            succes = art.add_genre(val)
            if not succes:
                reason=f"{val} is already saved as genre"
        else:
            succes = art.add_idol(val)
            if not succes:
                reason=f"{val} is already saved as idol"
    else: # the operation is remove
        if to_update == 'instrument':
            succes = art.remove_instrument(val)
            if not succes:
                reason=f"{val} is not saved as an instrument"
        elif to_update == 'genre':
            succes = art.remove_genre(val)
            if not succes:
                reason=f"{val} is not saved as genre"
        else:
            succes = art.remove_idol(val)
            if not succes:
                reason=f"{val} is not saved as an idol"
    if succes:
        art.save()

    return JsonResponse({'is_executed': succes, 'val': val, 'reason': reason})

@has_artist_profile
@login_required
@require_http_methods(['POST'])
def update_stage_name(request):
    """
    Ajax update for stage_name of an artist profile. The POST request must contain the key `val` which specifies
    the new stage_name of the corresponding Artist Profile.

    e.g. of a received json
    {
        'val': 'Slash'
    }

    This function returns a json with different keys
    1. 'is_executed' specifies whether the update request was executed succesfuly
    2. 'val' specifies the received new stage_name
    3. 'reason' specifies the reason for an eventual failure. Is empty when 'is_executed' is true
    4. 'old' specifies the old stage_name name
    {
        'is_executed': True,
        'val': 'Slash',
        'old': 'El loco',
        'reason': ''
    }
    """

    if not request.is_ajax():
        return JsonResponse({
            'is_executed': False,
            'val': '',
            'old': '',
            'reason': 'Request is not a Ajax post request'
        })

    new_sg = request.POST.get('val', False)
    if new_sg == '':
        return JsonResponse({
            'is_executed': False,
            'val': '',
            'old': '',
            'reason': 'The new stage_name is an empty string'
        })
    if not new_sg:
        return JsonResponse({
            'is_executed': False,
            'val': '',
            'old': '',
            'reason': 'No value was given for key val'
        })

    art= request.user.get_artist()
    old=art.stage_name
    if len(new_sg)> ArtistModel.MAX_LENGTH:
        return JsonResponse({
            'is_executed': False,
            'val': new_sg,
            'old': old,
            'reason': 'The Given stage_name is too long'
        })

    if new_sg == old:
        return JsonResponse({
            'is_executed': False,
            'val': new_sg,
            'old': old,
            'reason': "The new stage name didn't change"
        })

    art.stage_name=new_sg
    art.save()

    return JsonResponse({
        'is_executed': True,
        'val': new_sg,
        'old': old,
        'reason': ''
    })



@require_http_methods(['POST'])
@login_required
@has_artist_profile
def update_biography(request):
    """
    Ajax update for biography of an artist profile. The POST request must contain the key `val` which specifies
    the new biography of the corresponding Artist Profile.

    e.g. of a received json
    {
        'val': 'Hey My name is .....'
    }

    This function returns a json with different keys
    1. 'is_executed' specifies whether the update request was executed succesfuly
    2. 'val' specifies the received new biography
    3. 'reason' specifies the reason for an eventual failure. Is empty when 'is_executed' is true
    4. 'old' specifies the old biography
    {
        'is_executed': True,
        'val': 'Hey My name is .....',
        'old': 'Roses are blue ...',
        'reason': ''
    }
    """

    if not request.is_ajax():
        return JsonResponse({
            'is_executed': False,
            'val': '',
            'old': '',
            'reason': 'Request is not a Ajax post request'
        })

    new_bio = request.POST.get('val', False)
    if new_bio == '':
        return JsonResponse({
            'is_executed': False,
            'val': '',
            'old': '',
            'reason': 'The new biography is an empty string'
        })
    if not new_bio:
        return JsonResponse({
            'is_executed': False,
            'val': '',
            'old': '',
            'reason': 'No value was given for key val'
        })

    art= request.user.get_artist()
    old=art.biography

    art.biography=new_bio
    art.save()

    return JsonResponse({
        'is_executed': True,
        'val': new_bio,
        'old': old,
        'reason': ''
    })
