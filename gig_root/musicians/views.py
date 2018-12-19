import json

from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.utils.encoding import force_bytes, force_text
from django.template.loader import render_to_string
from django.contrib.sites.shortcuts import get_current_site
from django.shortcuts import render, redirect, reverse
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods

from artists.artist_util import has_artist_profile, is_band_owner
from users.models import User
from users.tokens import account_activation_token
from users.util import getHTTP_Protocol

from .forms import RegisterForm, DirectUploadProfilePicBand, DirectUploadBackgroundPicBand, DirectUploadBandPic, DirectVideoUpload, SoundCloudURL, SoundCloudPlayListURL, YoutubeURL, YoutubePlayListURL
from .models import Band, Member, BandPic, VideoBand
from users.templatetags.user_tags import fancy_date


def agenda(request, band_id):
    """
    The view that renders the agenda (all events) of band with id `band_id`.
    """

    band = Band.get_band(band_id)

    if not band:
        context= {'short_message': "The agenda of the band can't be loaded, because the provided band profile id does not exists.",
                  'title_msg': "Profile does not exists",
                  'title_page': "Bad request"}
        return render(request, 'users/short_message.html',context=context)

    context={
    'band': band,
    'upcoming_events': band.get_upcoming_events(),
    'past_events': band.get_past_events(),
    'is_owner': band.is_owner(request.user),
    'http_protocol': getHTTP_Protocol()
    }
    return render(request, 'musicians/agenda.html',context=context)



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
             'user_follows': band.is_follower(request.user),
             }

    return render(request, 'musicians/profile.html', context=context)


@require_http_methods(["GET", "POST"])
@login_required
@has_artist_profile
def register_band(request):
    """
    View to register a band profile.
    """
    f= RegisterForm()
    if request.method == 'POST':
        f=RegisterForm(request.POST, request.FILES)
        if f.is_valid():

            band = f.save(request.user.get_artist())
            band.add_member(request.user.get_artist(), is_active=True)

            return redirect('musicians:band-profile', profile_id=band.pk)

    context={'form': f}
    return render(request, 'musicians/register_band.html',context=context )

##############################################################################################
####
####    The following views are meant for ajax requests.
##############################################################################################

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
    """
    View meant to update the band description through Ajax request.

    The POST request needs to contain following keys:
    `val`: the new band description
    `band_id`: the id of the band for which this request is meant.

    The view response with a JSON containing following keys:
    `is_executed`: Boolean that tells whether the request executed succesfully.
    `reason`: contains a error message meant to inform the `user` or the `programmer`
    of the corresponding error.
    `val`: contains the new description
    """

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
    """
    View meant to update the band genres through Ajax request.

    The POST request needs to contain following keys:
    `val`: a genre to add or remove from the band information
    `band_id`: the id of the band for which this request is meant.
    'operation': which contains a value `add` or `remove`, which respectively adds `val`
    as a new genre that the band plays or removes `val` from de genres that the band plays.

    The view response with a JSON containing following keys:
    `is_executed`: Boolean that tells whether the request executed succesfully.
    `reason`: contains a error message meant to inform the `user` or the `programmer`
    of the corresponding error.
    `val`: the genre involved in the request
    """

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
    """
    View meant to update the role of a member or remove a member of a band through Ajax request.

    The POST request needs to contain following keys:
    `val`: the new role of a member (e.g. singer, drummer, and so on)
    `band_id`: the id of the band for which this request is meant.
    `operation`: contains the values `update` or `remove`, which respectively means that the role
    of the member is updated or the member is removed.
    `member_id`: the id of the 'Member' instance for which the request is meant.

    The view response with a JSON containing following keys:
    `is_executed`: Boolean that tells whether the request executed succesfully.
    `reason`: contains a error message meant to inform the `user` or the `programmer`
    of the corresponding error.
    `val`: contains the new description
    """

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
    """
    View meant to send an invitation email to an artist through Ajax request.
    The email will invite the user to click on a link in order to accept whether
    he/she desires to become member of the band. The link will be validated through
    `confirm_member` view.

    The POST request needs to contain following keys:
    `val`: the email of the artist that needs to be invited
    `band_id`: the id of the band for which this request is meant.

    The view response with a JSON containing following keys:
    `is_executed`: Boolean that tells whether the request executed succesfully.
    `reason`: contains a error message meant to inform the `user` or the `programmer`
    of the corresponding error.
    """

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
    """
    View that confirms an invitation link received by an artist through email.
    The view validate the link. And make the corresponding user, an official
    member of the corresponding band
    """
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
        video_pk = val
        try:
            VideoBand.objects.get(pk=video_pk).delete()
            return JsonResponse({'is_executed': True, 'val': video_pk})
        except:
            return JsonResponse({'is_executed': False, 'val':video_pk, 'reason': f'No Video with pk={video_pk}'})

    else: #add a new video
        metadata=json.loads(request.POST.get('val'))
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
    And also the expected by the __contains_failure

    Additionally when is_executed' is set to True, the following keys are returned;
     'val': the comment that was recently added,
     'date': the date when the comment was added,
     'first_name': the first name of the commentator
     'last_name': the last name of the commentator
     'comment_id': the identifier of the newly created comment
    """
    failure=__contains_failure(request, keys=['val'], only_owner=False)
    if failure:
        return failure

    comment=request.POST.get('val')
    band=Band.get_band(request.POST.get('band_id'))
    c=band.add_comment(msg=comment, commentator=request.user)

    return JsonResponse({'is_executed':True,
                          'val': c.comment,
                          'date': fancy_date(c.date),
                          'first_name': c.commentator.first_name,
                          'last_name': c.commentator.last_name,
                          'comment_id': c.pk})


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



@require_http_methods(["POST"])
@login_required
def update_follow(request):
    """
    Ajax request to follow or unfollow a band profile.
    The post request needs to contain the following keys;
    1. `val`: wich holds the value 'follow' or 'unfollow'.
    2. `band_id`: the identifier for the band involved in the ajax post request

    The user associated with the current session will `follow` or `unfollow` band
    with id `band_id`.

    If operation was executed returns a response with following keys:
    1. `is_executed`: a boolean that specifies wether the operation was executed
    2. 'followers': the new amount of followers for the band

    If the operation failed
    `reason` is provided instead of `followers`, which contains the reason for the failure

    """
    failure=__contains_failure(request, keys=['val'], only_owner=False)
    if failure:
        return failure

    val=request.POST.get('val')
    band=Band.get_band(request.POST.get('band_id'))

    if val == 'follow':
        band.add_follower(request.user) #The user is added as follower
    else: #unfollow
        band.remove_follower(request.user) #The user is removed from the follower


    return JsonResponse({'is_executed': True, 'followers': band.amount_followers})



@require_http_methods(["POST"])
@login_required
@has_artist_profile
def update_soundcloud_url(request):
    """
    Ajax request to update a sound cloud url associated to a band.
    The post request needs to contain the following keys;
    1. `val`: which holds the url.
    2. `band_id`: the identifier for the band involved in the ajax post request
    3. `kind_url`: the url that is involved in the request can be `profile` or `playlist`
    4. `operation`: which specifies the operation to be performed
        We have 3 different allowed operations
        a) profile-add; operation that add's an URL as the soundcloud profile url
        b) profile-update; operation that updates existings url to newly provided url
        c) profile-delete; operation that removes the url


    """
    failure=__contains_failure(request, keys=['val', 'kind_url'], allowed_operations=['add', 'update', 'delete'],only_owner=True)
    if failure:
        return failure

    kind_url = request.POST.get('kind_url')
    if kind_url not in ['profile', 'playlist']:
        return JsonResponse({'is_executed': False, 'reason': 'Only profile or playlist urls are accepted.'})

    url=request.POST.get('val')
    band=Band.get_band(request.POST.get('band_id'))
    operation=request.POST.get('operation')
    if operation == 'delete':
        if kind_url == 'profile':
            band.soundcloud_profile_url=None
            msg='URL to soundcloud profile succesfuly deleted.'
        else:
            band.soundcloud_playlist_url=None
            msg='URL to soundcloud playlist succesfuly deleted.'

        band.save()
        return JsonResponse({'is_executed': True, 'value': msg})

    f= SoundCloudURL({'url': url}) if kind_url == 'profile' else SoundCloudPlayListURL({'url': url})
    if not f.is_valid():
        errors=f.errors.as_data().get('url')
        error_msg=''
        for err in errors:
            error_msg+= '.'.join(err.messages)

            return JsonResponse({'is_executed': False, 'reason': error_msg})

    if kind_url == 'profile':
        band.soundcloud_profile_url=url
    else:
        band.soundcloud_playlist_url=url

    band.save()
    msg = 'url succesfuly added.' if operation == 'add' else 'url succesfuly updated.'

    return JsonResponse({'is_executed': True, 'value': msg})



@require_http_methods(["POST"])
@login_required
@has_artist_profile
def update_youtube_url(request):
    """
    Ajax request to update a youtube url associated to a band.
    The post request needs to contain the following keys;
    1. `val`: which holds the url.
    2. `band_id`: the identifier for the band involved in the ajax post request
    3. `kind_url`: the url that is involved in the request can be `channel` or `playlist`
    4. `operation`: which specifies the operation to be performed
        We have 3 different allowed operations
        a) profile-add; operation that add's an URL as the youtube channel url
        b) profile-update; operation that updates existings url to newly provided url
        c) profile-delete; operation that removes the url


    """
    failure=__contains_failure(request, keys=['val', 'kind_url'], allowed_operations=['add', 'update', 'delete'],only_owner=True)
    if failure:
        return failure

    kind_url = request.POST.get('kind_url')
    if kind_url not in ['channel', 'playlist']:
        return JsonResponse({'is_executed': False, 'reason': 'Only channel or playlist urls are accepted.'})

    url=request.POST.get('val')
    band=Band.get_band(request.POST.get('band_id'))
    operation=request.POST.get('operation')

    if operation == 'delete':
        if kind_url == 'channel':
            band.youtube_profile_url=None
            msg='URL to youtube channel succesfuly deleted.'
        else:
            band.youtube_playlist_url=None
            msg='URL to youtube playlist succesfuly deleted.'

        band.save()
        return JsonResponse({'is_executed': True, 'value': msg})

    f= YoutubeURL({'url': url}) if kind_url == 'channel' else YoutubePlayListURL({'url': url})
    if not f.is_valid():
        errors=f.errors.as_data().get('url')
        error_msg=''
        for err in errors:
            error_msg+= '.'.join(err.messages)

            return JsonResponse({'is_executed': False, 'reason': error_msg})

    if kind_url == 'channel':
        band.youtube_profile_url=url
    else:
        band.youtube_playlist_url=url

    band.save()
    msg = 'url succesfuly added.' if operation == 'add' else 'url succesfuly updated.'

    return JsonResponse({'is_executed': True, 'value': msg})


@require_http_methods(["POST"])
@login_required
@has_artist_profile
@is_band_owner
def delete_profile(request):
    """
    View that is called when a user desires to delete his/her band profile.
    The request is performed through Ajax.

    The POST request needs to contain following keys:
    'band_id': the id of the band that needs to be deleted

    The view response with a JSON containing following keys:
    `is_executed`: Boolean that tells whether the request was executed succesfully.
    `reason`: a error message only provided when `is_executed` is set to false.
    """
    failure=__contains_failure(request, keys=[], only_owner=True)
    if failure:
        return failure

    band=Band.get_band(request.POST.get('band_id'))
    band.delete()

    return JsonResponse({'is_executed': True})
