import json

from django.contrib.sites.shortcuts import get_current_site
from django.shortcuts import render, redirect, reverse
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods

from artists.artist_util import has_artist_profile
from users.models import User
from users.util import getHTTP_Protocol

from .forms import RegisterForm, DirectUploadProfilePicBand, DirectUploadBackgroundPicBand, DirectUploadBandPic
from .models import Band, Member, BandPic

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
             'line_up': band.get_active_members(),
             'band_pics': band.bandpic_set.all(), ##TODO sort e.g. by date
             'direct_pp': DirectUploadProfilePicBand(),
             'direct_bp': DirectUploadBackgroundPicBand(),
             'direct_pic': DirectUploadBandPic(),
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

            band = f.save(request.user.get_artist())
            band.add_member(request.user.get_artist(), is_active=True)

            return redirect('musicians:band-profile', profile_id=band.pk)

    context={'form': f}
    return render(request, 'musicians/register_band.html',context=context )


def __contains_failure(request, keys, allowed_operations=None):
    """
    Helper function that check common failure scenario's that occur during update of a band_profile
    """
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
            return JsonResponse({'is_executed': False, 'reason': 'A not supported operation was provided'})

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
def update_member(request):
    failure=__contains_failure(request, keys=['val', 'member_id'], allowed_operations=['update', 'remove'])
    if failure:
        return failure

    mem=Member.get_member(request.POST.get('member_id'))
    val=''
    if request.POST.get('operation')== 'update': #update the rol of a member
        val=request.POST.get('val')
        mem.role=val
        mem.save()
    else: #remove a member
        mem.delete()

    return JsonResponse({'is_executed': True, 'val': val})

@require_http_methods(["POST"])
@login_required
@has_artist_profile
def add_member(request):
    failure=__contains_failure(request, keys=['val'])
    if failure:
        return failure

    email= request.POST.get('val')
    user_toAdd=User.get_user(email, default=False)
    if not user_toAdd:
        return JsonResponse({'is_executed': False,
                            'reason': 'There is no user with that email address'})

    if not user_toAdd.has_artistProfile():
        return JsonResponse({'is_executed': False,
                            'reason': 'Invitation not sent. The user has currently no artist profile'})

    band=Band.get_band(request.POST.get('band_id'))
    if band.is_member(user_toAdd):#tests whether user_toAdd is already an active member
            return JsonResponse({'is_executed': False,
                                'reason': 'The user is already member of the band'})
    artistToAdd=user_toAdd.get_artist()
    if band.is_member(user_toAdd, only_active_members=False):
        #if this is true a Member instance already exists but the artistToAdd is an inactive member
        m=band.get_member(artistToAdd)
    else:
        #in this branch a Member instance don't exists
        m=band.add_member(role="Insert role specified", artist=artistToAdd, is_active=False)

    #TODO create a temporary token
    confirm_url=getHTTP_Protocol() + get_current_site(request).domain + reverse('musicians:confirm-membership', kwargs={'member_id': m.pk})
    mail_subject=f"Invitation to Join {band.name}"
    mail_message_txt= f"Hello {user_toAdd.first_name}, you received an invitaion to join {band.name}.\nClick on the following link to confirm the invitation {confirm_url}"
    user_toAdd.send_email(mail_subject=mail_subject, mail_message_txt=mail_message_txt)

    return JsonResponse({'is_executed': True, 'reason': 'An invitation was send succesfuly'})



@require_http_methods(["GET"])
@login_required
@has_artist_profile
def confirm_member(request, member_id):
    #TODO test the link towards a token

    mem=Member.get_member(member_id)
    if not mem:
        context= {'short_message': "The confirmation can't be executed because the passed identifier for the line up is incorrect .",
                  'title_msg': "The identifier of the lineup is incorrect",
                  'title_page': "Bad request"}
        return render(request, 'users/short_message.html',context=context)

    if mem.artist != request.user.get_artist():
            context= {'short_message': "The request can't be executed because you are not allowed to request this page.",
                      'title_msg': "You tried to perform an unauthorized operation.",
                      'title_page': "Bad request"}
            return render(request, 'users/short_message.html',context=context)

    if not mem.is_active:
        mem.is_active= True
        mem.save()

    return redirect('musicians:band-profile', profile_id=mem.get_band().pk)

@require_http_methods(["POST"])
@login_required
@has_artist_profile
def update_picture(request):
    """
    Ajax request to perform some operation on a picture belonging to the band.
    The post request needs to contain the following keys;
    1. `operation`: which represents the operation to perform.
    2. `val`: the value needed to perform the operation
    3. `band_id`: the band identifier for which the operation needs to be performed

    The following operations are allowed:
    `delete`: will delete a `band picture` of `band_id`, val corresponds with the `public_id` of the pic to be deleted
    `add`: will add a picture to the `band_pics` of `band_id`, val corresponds with the metadata of the pic
    `profile`: will update the profile_picture of `band_id`, `val` corresponds with the metadata of the pic
    `background`: will update the background_picture of `band_id`, `val` corresponds with the metadata of the pic
    """
    failure=__contains_failure(request, keys=['val'], allowed_operations=['delete', 'add', 'profile', 'background'])
    if failure:
        return failure

    operation=request.POST.get('operation')
    val=request.POST.get('val')
    band=Band.get_band(request.POST.get('band_id'))
    if operation == 'profile' or operation =='background':
        metadata=json.loads(request.POST.get('val'))
        pic= band.profile_pic if operation == 'profile' else band.background_pic
        pic.update_metadata(public_id=metadata.get('public_id'),
                            title=metadata.get('original_filename'),
                            width=metadata.get('width'),
                            height=metadata.get('height'))

        pic.save()

        return JsonResponse({'is_executed': True, 'val': metadata.get('url')})

    elif operation == 'delete':
        pic_pk = val
        try:
            BandPic.objects.get(pk=pic_pk).delete()
            return JsonResponse({'is_executed': True, 'val': pic_pk})
        except:
            return JsonResponse({'is_executed': False, 'val':pic_pk, 'reason': f'No picture with pk={pic_pk}'})

    else: #add a new picutre case
        metadata=json.loads(request.POST.get('val'))
        pic=BandPic(band=band,
                    public_id=metadata.get('public_id'),
                    title=metadata.get('original_filename'),
                    width=metadata.get('width'),
                    height=metadata.get('height'))
        pic.save()
        return JsonResponse({'is_executed': True, 'val': metadata.get('url')})
