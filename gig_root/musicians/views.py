import json

from django.contrib.sites.shortcuts import get_current_site
from django.shortcuts import render, redirect, reverse
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods

from artists.artist_util import has_artist_profile
from users.models import User
from users.util import getHTTP_Protocol

from .forms import RegisterForm, DirectUploadProfilePicBand, DirectUploadBackgroundPicBand, DirectUploadBandPic, DirectVideoUpload
from .models import Band, Member, BandPic, VideoBand

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
             'band_videos': band.get_video_set(),
             'direct_pp': DirectUploadProfilePicBand(),
             'direct_bp': DirectUploadBackgroundPicBand(),
             'direct_pic': DirectUploadBandPic(),
             'direct_video': DirectVideoUpload(),
             'comments': band.get_comments(),
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


def __contains_failure(request, keys, allowed_operations=None, only_owner=True):
    """
    Helper function that check common failure scenario's that occur during update of a band_profile through Ajax request.

    This functions checks the following cases;
    1. The request is an ajax request
    2. Makes sure that the values for the list of `keys` were provided in the POST request
    and that the values are not empty strings
    3. Makes sure that the post request contains the key `band_id`, which refers to the band primary key involved in the
    operation, and that the band exists
    4. if only_owner is set to True, only requests coming from the owner of the band are allowed
    5. IF allowed_operations is not None, a key `operation` is expected in the POST request and checks whether the associated value
    is contained in the list of allowed operations

    If no failure occurs the function returns False
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

    if only_owner:
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

from users.tokens import account_activation_token
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.utils.encoding import force_bytes, force_text
from django.template.loader import render_to_string
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

    context={'user': user_toAdd,
            'band': band,
            'http_protocol': getHTTP_Protocol(),
            'domain': get_current_site(request).domain,
            'token': account_activation_token.make_token(user_toAdd),
            'uid': urlsafe_base64_encode(force_bytes(user_toAdd.pk)).decode(),
            'mid64': urlsafe_base64_encode(force_bytes(m.pk)).decode()
            }

    mail_subject=f"Invitation to Join {band.name}"
    mail_message_txt = render_to_string('musicians/messages/confirm_band_join.txt', context=context)
    user_toAdd.send_email(mail_subject=mail_subject, mail_message_txt=mail_message_txt)

    return JsonResponse({'is_executed': True, 'reason': 'An invitation was send succesfuly'})



@require_http_methods(["GET"])
@login_required
@has_artist_profile
def confirm_member(request, uidb64, token, mid64):
    try:
        uid = force_text(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
        member_id=force_text(urlsafe_base64_decode(mid64))
        membership=Member.objects.get(pk=member_id)
    except(TypeError, ValueError, OverflowError, User.DoesNotExist):
        user=None
        membership=None

    if user is None or membership is None or not account_activation_token.check_token(user, token):
        context= {'short_message': "You seem to have an invalid link. Check if you are logged in with a correct profile.\nIf the problem persists ask the band owner to send you another invation link.",
                  'title_msg': "Activation link is invalid!.",
                  'title_page': "Bad request"}
        return render(request, 'users/short_message.html',context=context)

    if user.pk != request.user.pk:
        context= {'short_message': "You are trying to perform a request not meant for you. Check if you are logged in with a correct profile.",
                  'title_msg': "Unauhtorized request",
                  'title_page': "Bad request"}
        return render(request, 'users/short_message.html',context=context)

    band=membership.get_band()

    if  membership.is_active:
        return redirect('musicians:band-profile', profile_id=band.pk)

    membership.is_active= True
    membership.save()
    context= {'short_message': f"You are officialy registered as member of {band.name}. Take a look at your band profile ",
              'title_msg': "Confirmation complete",
              'title_page': f"{band.name}",
              'link': reverse('musicians:band-profile', kwargs={'profile_id': band.pk}),
              }
    return render(request, 'users/short_message.html',context=context)


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
        print(f"type public_id {type(metadata.get('public_id'))}")
        pic=BandPic(band=band,
                    public_id=metadata.get('public_id'),
                    title=metadata.get('original_filename'),
                    width=metadata.get('width'),
                    height=metadata.get('height'))
        pic.save()
        return JsonResponse({'is_executed': True, 'val': metadata.get('url')})


@require_http_methods(["POST"])
@login_required
@has_artist_profile
def update_video(request):
    """
    Ajax request to perform an `add` or `delete` operation of a video.
    The post request needs to contain the following keys;
    1. `operation`: which represents the operation to perform.
    2. `val`: the value needed to perform the operation
    3. `band_id`: the band identifier for which the operation needs to be performed

    The following operations are allowed:
    `delete`: will delete a `band vide` of `band_id`, val corresponds with the `public_id` of the video to be deleted
    `add`: will add a VideoBand instance for band with `band_id`, val corresponds with the metadata of the video.

    """
    failure=__contains_failure(request, keys=['val'], allowed_operations=['delete', 'add'])
    if failure:
        return failure

    operation=request.POST.get('operation')
    val=request.POST.get('val')
    band=Band.get_band(request.POST.get('band_id'))

    if operation == 'delete':
        print("delete")
        video_pk = val
        try:
            VideoBand.objects.get(pk=video_pk).delete()
            return JsonResponse({'is_executed': True, 'val': video_pk})
        except:
            return JsonResponse({'is_executed': False, 'val':video_pk, 'reason': f'No Video with pk={video_pk}'})

    else: #add a new video
        metadata=json.loads(request.POST.get('val'))
        print("ADD")
        print(f"type public_id {type(metadata.get('public_id'))}")
        vid=VideoBand(band=band, public_id=metadata.get('public_id'), title=metadata.get('original_filename'))
        vid.save()
        return JsonResponse({'is_executed': True, 'val': metadata.get('url')})


@require_http_methods(["POST"])
@login_required
def add_comment(request):
    """
    Ajax request to add a comment.
    The post request needs to contain the following keys;
    1. `val`: the comment that needs to be added

    """
    failure=__contains_failure(request, keys=['val'], only_owner=False)
    if failure:
        return failure

    comment=request.POST.get('val')
    band=Band.get_band(request.POST.get('band_id'))
    c=band.add_comment(msg=comment, commentator=request.user)

    return JsonResponse({'is_executed':True,
                          'val': c.comment,
                          'date': c.date,
                          'first_name': c.commentator.first_name,
                          'last_name': c.commentator.last_name,})


@require_http_methods(["POST"])
@login_required
def vote_comment(request):
    """
    Ajax request to upvote or downvote a comment.
    The post request needs to contain the following keys;
    1. `val`: the comment_id that needs to be upvoted or downvoted
    2. `operation`: 'upvote' or 'downvote'

    If operation was executed returns a response with following keys:
    1.'upvotes': the new amount of total upvotes for the comment
    2.'downvotes': the new amount of total downvotes for the comment

    """
    failure=__contains_failure(request, keys=['val'], allowed_operations=['upvote', 'downvote'], only_owner=False)
    if failure:
        return failure

    operation=request.POST.get('operation')
    band=Band.get_band(request.POST.get('band_id'))
    comment_id=request.POST.get('val')
    c=band.get_comment(comment_id)
    if not c:
        return JsonResponse({'is_executed': False, 'reason': f'Comment with pk {comment_id} does not exists'})

    if operation == 'upvote':
        if not c.upvote(request.user): #The user already voted for this comment
            if not c.get_vote(request.user).is_upvote:
                c.inverse_vote(request.user)
    else: #downvote
        if not c.downvote(request.user):
            if c.get_vote(request.user).is_upvote:
                c.inverse_vote(request.user)

    return JsonResponse({'is_executed': True, 'upvotes': c.upvotes, 'downvotes': c.downvotes})



@require_http_methods(["POST"])
@login_required
def vote_band(request):
    """
    Ajax request to upvote or downvote a band profile.
    The post request needs to contain the following keys;
    1. `operation`: 'upvote' or 'downvote'

    If operation was executed returns a response with following keys:
    1.'upvotes': the new amount of total upvotes for the band
    2.'downvotes': the new amount of total downvotes for the band

    """
    failure=__contains_failure(request, keys=[], allowed_operations=['upvote', 'downvote'], only_owner=False)
    if failure:
        return failure

    operation=request.POST.get('operation')
    band=Band.get_band(request.POST.get('band_id'))

    if operation == 'upvote':
        if not band.upvote(request.user): #The user already voted for this band
            if not band.get_vote(request.user).is_upvote:
                band.inverse_vote(request.user)
    else: #downvote
        if not band.downvote(request.user):
            if band.get_vote(request.user).is_upvote:
                band.inverse_vote(request.user)

    return JsonResponse({'is_executed': True, 'upvotes': band.upvotes, 'downvotes': band.downvotes})
