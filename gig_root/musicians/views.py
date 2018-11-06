from django.contrib.sites.shortcuts import get_current_site
from django.shortcuts import render, redirect, reverse
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods

from artists.artist_util import has_artist_profile
from users.models import User
from users.util import getHTTP_Protocol

from .forms import RegisterForm
from .models import Band, LinupMember

def test(request):
    return HttpResponse("Received reuqest")



def band_profile(request, profile_id):
    """
    The view that renders a band profile based on a `profile_id`.
    If the requester is the owner of the band, a base template is augmented with `manage band profile`
    tags.
    """

    band = Band.get_band(profile_id)

    if not band:
        context= {'short_message': "The requested band profile does not exists.",
                  'title_msg': "Profile does not exists",
                  'title_page': "Bad request"}
        return render(request, 'users/short_message.html',context=context)

    #Here we are certain that Band with private key `profile_id` exists


    #is_owner tells wheter the user accessing band profile is the owner of that band profile
    is_owner = band.is_owner(request.user)

    #is_member tells whether the user accessing band profile is a member of the band
    is_member=band.is_member(request.user)

    email= band.get_contact_email()

    context={'band': band,
             'contact_email': email,  #needed to contact the band
             'is_owner': is_owner,
             'is_member': is_member,
             'line_up_set': band.get_active_members(),
             'band_pics': band.band_pics, ##TODO sort e.g. by date
             }

    return render(request, 'musicians/profile.html', context=context)


@require_http_methods(["GET", "POST"])
@login_required
@has_artist_profile
def register_band(request):
    f= RegisterForm()
    if request.method == 'POST':
        f=RegisterForm(request.POST, request.FILES)
        if f.is_valid():
            #saves the band information and profile and bg picture of the band
            band = f.save(request.user.get_artist())
            lm=LinupMember(role="insert your role", member=request.user.get_artist(), band=band, is_active=True)
            lm.save()
            return redirect('musicians:band-profile', profile_id=band.pk)

    context={'form': f}
    return render(request, 'musicians/register_band.html',context=context )


def __contains_failure(request, keys, allowed_operations=None):
        if not request.is_ajax():
            context={
                'title_page': 'Bad Request',
                'title_msg': 'The requested operation is unauthorized',
                'short_message': 'The requested operation is unauthorized'
            }
            return render(request, 'users/short_message.html', context=context)

        for key in keys:
            val= request.POST.get(key, False)
            if not val:
                return JsonResponse({'is_executed': False,
                                    'reason': f'no value for key {key} was provided in the post request'})

            if val == '':
                return JsonResponse({'is_executed': False,
                                    'reason': f'The value for key {key} cannot be an empty string'})

        band_id=request.POST.get('band_id', False)

        if not band_id:
            return JsonResponse({'is_executed': False,
                                 'reason': 'No band id was provided'})

        band= Band.get_band(band_id)
        if not band:
            return JsonResponse({'is_executed': False,
                                'reason': f'No band with band id {band_id} stored in the database.'})

        if not band.is_owner(request.user):
            return JsonResponse({'is_executed': False,
                                'reason': f'Unauhtorized request'})

        if allowed_operations:
            operation= request.POST.get('operation', False)
            if not operation:
                return JsonResponse({'is_executed': False, 'reason': 'no operation was specified'})

            if not (operation in allowed_operations):
                return JsonResponse({'is_executed': False, 'reason': 'An non supported operation was provided'})

        return False

@require_http_methods(["POST"])
@login_required
@has_artist_profile
def update_description(request):

    failure=__contains_failure(request, keys=['val'])
    if failure:
        return failure

    new_desc=request.POST.get('val')
    band=Band.get_band(request.POST.get('band_id'))
    band.description=new_desc
    band.save()

    return JsonResponse({'is_executed': True, 'val': new_desc})

@require_http_methods(["POST"])
@login_required
@has_artist_profile
def update_genre(request):

    failure=__contains_failure(request, keys=['val'], allowed_operations=['add', 'remove'])
    if failure:
        return failure

    val=request.POST.get('val')
    band=Band.get_band(request.POST.get('band_id'))
    reason=''
    if request.POST.get('operation')=='add':
        is_executed=band.add_genre(val)
        if not is_executed:
            reason='genre is already saved'
    else:
        is_executed=band.remove_genre(val)
        if not is_executed:
            reason='genre was never part of the band'

    band.save()

    return JsonResponse({'is_executed': is_executed, 'val': val, 'reason': reason})

@require_http_methods(["POST"])
@login_required
@has_artist_profile
def update_line_up(request):
    failure=__contains_failure(request, keys=['val', 'line_up_id'], allowed_operations=['update', 'remove'])
    if failure:
        return failure

    line_up=LinupMember.get_line_up(request.POST.get('line_up_id'))
    val=''
    if request.POST.get('operation')== 'update': #update the rol of a memeber
        val=request.POST.get('val')
        line_up.role=val
        line_up.save()
    else: #remove a member
        line_up.delete()

    return JsonResponse({'is_executed': True, 'val': val})

@require_http_methods(["POST"])
@login_required
@has_artist_profile
def add_member(request):
    failure=__contains_failure(request, keys=['val'])
    if failure:
        return failure

    email= request.POST.get('val')
    user=User.get_user(email, default=False)
    if not user:
        return JsonResponse({'is_executed': False,
                            'reason': 'There is no user with that email address'})

    if not(user.has_artistProfile()):
        return JsonResponse({'is_executed': False,
                            'reason': 'Invitation not sent. The user has currently no artist profile'})

    band=Band.get_band(request.POST.get('band_id'))
    if band.is_member(user):
            return JsonResponse({'is_executed': False,
                                'reason': 'Invitation not sent. The user is already member of the band'})
    artist=user.get_artist()
    if band.is_member(user, only_active_members=False):
        #if this is true then an LineUpMember instance already exists for the artist.
        l=band.get_line_up(artist)
    else:
        l=LinupMember(role="Insert role specified", member=artist, band=band, is_active=False)
        l.save()

    #TODO create a temporary token
    confirm_url=getHTTP_Protocol() + get_current_site(request).domain + reverse('musicians:confirm-membership', kwargs={'line_up_id': l.pk})
    mail_subject=f"Invitation to Join {band.name}"
    mail_message_txt= f"Hello {user.first_name}, you received an invitaion to join {band.name}.\nClick on the following link to confirm the invitation {confirm_url}"
    user.send_email(mail_subject=mail_subject, mail_message_txt=mail_message_txt)

    print(mail_message_txt)

    return JsonResponse({'is_executed': True, 'reason': 'An invitation was send succesfuly'})



@require_http_methods(["GET"])
@login_required
@has_artist_profile
def confirm_member(request, line_up_id):
    #TODO test the link towards a token

    lin=LinupMember.get_line_up(line_up_id)
    if not lin:
        context= {'short_message': "The confirmation can't be executed because the passed identifier for the line up is incorrect .",
                  'title_msg': "The identifier of the lineup is incorrect",
                  'title_page': "Bad request"}
        return render(request, 'users/short_message.html',context=context)

    if lin.member != request.user.get_artist():
            context= {'short_message': "The request can't be executed because you are not allowed to request this page.",
                      'title_msg': "You tried to perform an unauthorized operation.",
                      'title_page': "Bad request"}
            return render(request, 'users/short_message.html',context=context)

    if not lin.is_active:
        lin.is_active= True
        lin.save()

    return redirect('musicians:band-profile', profile_id=lin.band.pk)
