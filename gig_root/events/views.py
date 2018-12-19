import json

from django.utils import timezone
from django.core.mail import EmailMessage
from django.shortcuts import render, redirect, reverse
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib.sites.shortcuts import get_current_site
from django.views.decorators.http import require_http_methods
from django.template.loader import render_to_string

from artists.artist_util import has_artist_profile, is_band_owner
from musicians.models import Band
from users.util import getHTTP_Protocol
from .forms import CreateEventForm, DirectUploadPic
from .models import Event, str_to_int
from users.templatetags.user_tags import fancy_date


def event_details(request, event_id):
    """
    View that displays the essential information about event with id `event_id`;
    e.g. name, time, date, address,..
    Additionaly the address is displayed on a map.
    """
    try:
        event=Event.objects.get(pk=event_id)
    except:
        context= {'short_message': "You are trying to access an event page that does not exist.",
                  'title_msg': f"Event does not exist",
                  'titple_page': "Bad request",
                  }
        return render(request, 'users/short_message.html', context=context)


    context={
            'event': event,
            'http_protocol': getHTTP_Protocol(),
            }

    return render(request, 'events/event_details.html', context=context)

def event_profile(request, event_id):
    """
    View that renders event with id `event_id`
    """
    try:
        event=Event.objects.get(pk=event_id)
    except:
        context= {'short_message': "You are trying to access an event page that does not exist.",
                  'title_msg': f"Event does not exist",
                  'titple_page': "Bad request",
                  }
        return render(request, 'users/short_message.html', context=context)

    band=event.band

    context={
            'event': event,
            'band': band,
            'user': request.user,
            'is_owner': event.is_owner(request.user),
            'comments': event.get_comments(),
            'participants': event.get_participants(),
            'is_participant': event.is_participant(request.user),
            }

    return render(request, 'events/event.html', context=context)


@require_http_methods(["GET", "POST"])
@login_required
@has_artist_profile
@is_band_owner
def create_event(request):
    """
    View to create an upcoming event for a band. The user requesting this page
    is required to be the owner of at least one band.

    Additionaly, the form requires two hidden_fields to be automatically filled at the client side.
    The value provided at `address` field by the user needs to be transformed into
    latitude and longitude values, which are used to populate the two hidden_fields: `latitude` and `longitude`
    """

    artist=request.user.get_artist()
    bands=artist.owns.all()

    if request.method == 'POST':
        f=CreateEventForm(request.POST, request.FILES, bands=bands)
        if f.is_valid():
            f.save(commit=False)
            f.savePicture()
            f.instance.save()
            return redirect('events:profile', event_id=f.instance.pk)

        return render(request, "events/create.html",{'form': f})


    f=CreateEventForm(bands=bands)
    return render(request, "events/create.html",{'form': f})



@require_http_methods(["GET"])
@login_required
@has_artist_profile
@is_band_owner
def event_edit(request, event_id):
    """
    View meant for the editing of an event with id `event_id`.
    """

    try:
        event=Event.objects.get(pk=event_id)
    except:
        context= {'short_message': "You are trying to edit an event page that does not exist.",
                  'title_msg': f"Event does not exist",
                  'titple_page': "Bad request",
                  }
        return render(request, 'users/short_message.html', context=context)


    if not event.is_owner(request.user):
        context= {'short_message': "You are trying to edit an event that does not belong to you.",
                  'title_msg': f"Unauthorized request ",
                  'titple_page': "Bad request",
                  }
        return render(request, 'users/short_message.html', context=context)

    artist=request.user.get_artist()
    context= {'event': event,
              'current_band':event.band,
              'remaining-bands': artist.owns.all(),
              'directPicForm': DirectUploadPic()}
    return render(request, "events/edit_event.html",context=context)

##########################################################################
###
###         THE FOLLOWING REQUEST ARE AJAXS REQUESTS
###
#########################################################################


def __contains_failure(request, keys, allowed_operations=None, only_owner=True):
    """
    Helper function that check common failure scenario's that occur during update of a event_profile through Ajax request.

    This functions checks the following cases;
    1. The request is an ajax request
    2. Makes sure that the values for the list of `keys` were provided in the POST request
    and that the values are not empty strings
    3. Makes sure that the post request contains the key `event_id`, which refers to the event primary key involved in the
    operation, and that the event exists
    4. IF allowed_operations is not None, a key `operation` is expected in the POST request and checks whether the associated value
    is contained in the list of allowed operations
    5. If only_owner is set to true, the request is only allowed for the owner of the event.

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

    event_id=request.POST.get('event_id', False)

    if not event_id:
        return JsonResponse({'is_executed': False,
                             'reason': 'No event id was provided'})

    try:
        event=Event.objects.get(pk=event_id)
    except:
        return JsonResponse({'is_executed': False,
                            'reason': f'No event with event id {event_id} stored in the database.'})

    if only_owner and not event.is_owner(request.user):
        return JsonResponse({'is_executed': False,
                            'reason': f'Unauhtorized request'})

    if allowed_operations:
        operation= request.POST.get('operation', False)
        if not operation:
            return JsonResponse({'is_executed': False, 'reason': 'no operation was specified'})

        if not (operation in allowed_operations):
            return JsonResponse({'is_executed': False, 'reason': 'A not supported operation was provided'})

    return False

def __is_valid_name(name):
    """
    private function to validate event name provided trough ajax request.
    """
    if name == '':
        return {'valid': False, 'reason': 'new name cannot be an empty string.'}
    if len(name) > Event.MAX_LENGTH_NAME:
        return {'valid': False, 'reason': f'new name is too long (max. {Event.MAX_LENGTH_NAME} chars allowed).'}
    return {'valid': True}

@require_http_methods(["POST"])
@login_required
@has_artist_profile
@is_band_owner
def update_name(request):
    """
    View meant to update the event name through Ajax request.

    The POST request needs to contain following keys:
    `val`: the new name for the event
    `event_id`: the id of the event for which the name needs to change.

    The view response with a JSON containing following keys:
    `is_executed`: Boolean that tells whether the update executed succesfully.
    `reason`: contains a error message meant to inform the `user` or the `programmer`
    of the corresponding error.
    """
    failure=__contains_failure(request, keys=['val'])
    if failure:
        return failure

    event=Event.objects.get(pk=request.POST.get('event_id'))
    name=request.POST.get('val')
    valid= __is_valid_name(name)
    if not valid.get('valid'):
        return JsonResponse({'is_executed': False, 'reason': valid.get('reason')})

    event.name=name
    event.save()
    return JsonResponse({'is_executed': True})



def __is_valid_description(description):
    """
    private function to validate event description provided trough ajax request.
    """
    if description == '':
        return {'valid': False, 'reason': 'new description cannot be an empty string.'}
    return {'valid': True}

@require_http_methods(["POST"])
@login_required
@has_artist_profile
@is_band_owner
def update_description(request):
    """
    View meant to update the event description through Ajax request.

    The POST request needs to contain following keys:
    `val`: the new description for the event
    `event_id`: the id of the event for which the description needs to change.

    The view response with a JSON containing following keys:
    `is_executed`: Boolean that tells whether the update executed succesfully.
    `reason`: contains a error message meant to inform the `user` or the `programmer`
    of the corresponding error.
    """

    failure=__contains_failure(request, keys=['val'])
    if failure:
        return failure

    event=Event.objects.get(pk=request.POST.get('event_id'))
    description=request.POST.get('val')
    valid= __is_valid_description(description)
    if not valid.get('valid'):
        return JsonResponse({'is_executed': False, 'reason': valid.get('reason')})

    event.description=description
    event.save()
    return JsonResponse({'is_executed': True})

def __is_valid_date(date_str):
    """
    private function to validate event date provided trough ajax request.
    """
    format_str = '%Y-%m-%d' # The format
    try:
        datetime_obj = timezone.datetime.strptime(date_str, format_str)
    except:
        return {'valid': False, 'reason': 'new date has incorrect format.'}

    now=timezone.now()
    datetime_obj=timezone.datetime(datetime_obj.year, datetime_obj.month, datetime_obj.day, 0, 30, 30, 30, now.tzinfo)
    if datetime_obj.date() < now.date():
        return {'valid': False, 'reason': 'date cannot be in the past.'}

    return {'valid': True, 'datetime': datetime_obj}

@require_http_methods(["POST"])
@login_required
@has_artist_profile
@is_band_owner
def update_date(request):
    """
    View meant to update the event date through Ajax request.

    The POST request needs to contain following keys:
    `val`: the new date for the event
    `event_id`: the id of the event for which the date needs to change.

    The view response with a JSON containing following keys:
    `is_executed`: Boolean that tells whether the update executed succesfully.
    `reason`: contains a error message meant to inform the `user` or the `programmer`
    of the corresponding error.
    """

    failure=__contains_failure(request, keys=['val'])
    if failure:
        return failure

    event=Event.objects.get(pk=request.POST.get('event_id'))
    date=request.POST.get('val')
    valid= __is_valid_date(date)
    if not valid.get('valid'):
        return JsonResponse({'is_executed': False, 'reason': valid.get('reason')})

    d=valid.get('datetime')

    dt=timezone.datetime(d.year, d.month, d.day, event.date.hour, event.date.minute, event.date.second, event.date.microsecond, d.tzinfo)
    event.date=dt
    event.save()
    return JsonResponse({'is_executed': True})


def __is_valid_time(time_str, current_date):
    """
    private function to validate event time provided trough ajax request.
    """
    try:
        time=timezone.datetime.strptime(time_str, '%H:%M').time()
    except:
        return {'valid': False, 'reason': 'new time has incorrect format.'}

    now = timezone.now()
    new_d= timezone.datetime(current_date.year, current_date.month, current_date.day, time.hour, time.minute, time.second, time.microsecond, now.tzinfo)
    if new_d < now:
         return {'valid': False, 'reason': f'time and date cannot be in the past. Given {new_d}'}

    return {'valid': True, 'datetime': new_d}

@require_http_methods(["POST"])
@login_required
@has_artist_profile
@is_band_owner
def update_time(request):
    """
    View meant to update the event time through Ajax request.

    The POST request needs to contain following keys:
    `val`: the new time for the event
    `event_id`: the id of the event for which the time needs to change.

    The view response with a JSON containing following keys:
    `is_executed`: Boolean that tells whether the update executed succesfully.
    `reason`: contains a error message meant to inform the `user` or the `programmer`
    of the corresponding error.
    """

    failure=__contains_failure(request, keys=['val'])
    if failure:
        return failure

    event=Event.objects.get(pk=request.POST.get('event_id'))
    time=request.POST.get('val')
    valid= __is_valid_time(time, event.date)
    if not valid.get('valid'):
        return JsonResponse({'is_executed': False, 'reason': valid.get('reason')})

    d=valid.get('datetime')
    event.date=d
    event.save()
    return JsonResponse({'is_executed': True})



def __is_valid_band(band_pk, artist):
    """
    private function to validate the band associated to the event provided through ajax request.
    """
    try:
        band_pk=str_to_int(band_pk)
    except:
        return {'valid': False, 'reason': 'identifier of band is incorrect.'}

    if not artist.owns.all().filter(pk=band_pk).exists():
        return {'valid': False, 'reason': 'incorrect choice of band.'}
    return {'valid': True}


@require_http_methods(["POST"])
@login_required
@has_artist_profile
@is_band_owner
def update_band(request):
    """
    View meant to update the band associated with a particular event through Ajax request.

    The POST request needs to contain following keys:
    `val`: the new band id for the event
    `event_id`: the id of the event for which the associated band needs to change.

    The view response with a JSON containing following keys:
    `is_executed`: Boolean that tells whether the request was executed succesfully.
    `reason`: contains a error message meant to inform the `user` or the `programmer`
    of the corresponding error.
    """

    failure=__contains_failure(request, keys=['val'])
    if failure:
        return failure

    event=Event.objects.get(pk=request.POST.get('event_id'))
    new_band_pk=request.POST.get('val')
    valid= __is_valid_band(new_band_pk, request.user.get_artist())
    if not valid.get('valid'):
        return JsonResponse({'is_executed': False, 'reason': valid.get('reason')})

    event.band=Band.get_band(pk=new_band_pk)
    event.save()
    return JsonResponse({'is_executed': True})

@require_http_methods(["POST"])
@login_required
@has_artist_profile
@is_band_owner
def update_picture(request):
    """
    View meant to update the picture of an event through Ajax request.
    And is called after the new picture was uploaded to Cloudinary through client-side.

    The POST request needs to contain following keys:
    `val`: the metadata of the new picture uploaded through the client side
    `event_id`: the id of the event for which the picture needs to change.

    The view response with a JSON containing following keys:
    `is_executed`: Boolean that tells whether the request was executed succesfully.
    `reason`: contains a error message meant to inform the `user` or the `programmer`
    of the corresponding error.
    """
    failure=__contains_failure(request, keys=['val'])
    if failure:
        return failure

    event=Event.objects.get(pk=request.POST.get('event_id'))
    metadata=json.loads(request.POST.get('val'))

    event.picture.update_metadata(public_id=metadata.get('public_id'),
                                  title=metadata.get('original_filename'),
                                  width=metadata.get('width'),
                                  height=metadata.get('height'))

    event.picture.save()
    return JsonResponse({'is_executed': True})

@require_http_methods(["POST"])
@login_required
def add_comment(request):
    """
    View meant to add a comment to an event through Ajax request.

    The POST request needs to contain following keys:
    `val`: the comment message
    `event_id`: the id of the event for which a comment is added.

    The view response with a JSON containing following keys:
    `is_executed`: Boolean that tells whether the request was executed succesfully.
    `reason`: contains a error message meant to inform the `user` or the `programmer`
    of the corresponding error.

    Additionaly When `is_executed` is set to true, the following is also returned;
    'comment': the comment added,
    'commentator': the first and last_name of the commentator
    'date': The date when the comment was added
    'comment_id': the identifier of the comment being added.
    'downvotes': the amount of downvotes for this comment (equal to 0)
    'upvotes': the amount of upvotes for this comment (equal to 0)
    """

    failure=__contains_failure(request, keys=['val'], only_owner=False)
    if failure:
        return failure

    event=Event.objects.get(pk=request.POST.get('event_id'))
    msg=request.POST.get('val')

    com= event.add_comment(msg, commentator=request.user)
    jsonRes={
        'is_executed': True,
        'comment': com.comment,
        'commentator': str(com.commentator),
        'date': fancy_date(com.date),
        'comment_id': com.pk,
        'downvotes': com.downvotes,
        'upvotes': com.upvotes,
    }
    return JsonResponse(jsonRes)

@require_http_methods(["POST"])
@login_required
def vote_comment(request):
    """
    View meant to upvote or downvote a comment associated to an event through Ajax request.

    The POST request needs to contain following keys:
    `val`: the ID of the comment that is being upvoted or downvoted
    `event_id`: the id of the event for which a comment is being up/downvoted.
    `operation`: wich contains the value `upvote` or `downvote` to respectively upvote or downvote the comment

    The view response with a JSON containing following keys:
    `is_executed`: Boolean that tells whether the request was executed succesfully.
    `reason`: contains a error message meant to inform the `user` or the `programmer`
    of the corresponding error.

    Additionaly When `is_executed` is set to true, the following is also returned;
    `upvotes`: containes the new amount of upvotes
    `downvotes`: containes the new amount of downvotes
    """

    failure=__contains_failure(request, keys=['val'], allowed_operations=['upvote', 'downvote'], only_owner=False)
    if failure:
        return failure

    operation=request.POST.get('operation')
    event=Event.objects.get(pk=request.POST.get('event_id'))
    comment_id=request.POST.get('val')
    c=event.get_comment(comment_id)
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
def update_participation(request):
    """
    View meant to mark a user as participant for an event or mark his/her disengage for the event through Ajax request.

    The POST request needs to contain following keys:
    `event_id`: the id of the event for which a user is added/removed as participant of the event.
    `operation`: a value equal to `participate` or `disengage` to respectively add the user or remove
    the user of the Participants set.

    The view response with a JSON containing following keys:
    `is_executed`: Boolean that tells whether the request was executed succesfully.
    `participants`: a intiger with the new amount of participants after the request was executed succesfully
    `reason`: contains a error message meant to inform the `user` or the `programmer`
    of the corresponding error.
    """
    failure=__contains_failure(request, keys=[], allowed_operations=['participate', 'disengage'], only_owner=False)
    if failure:
        return failure

    operation=request.POST.get('operation')
    event=Event.objects.get(pk=request.POST.get('event_id'))

    if operation == 'participate':
        event.add_participant(request.user)
    else: #disengage
        event.remove_participant(request.user)

    return JsonResponse({'is_executed': True, 'participants': event.amount_participants})

def __is_valid_email(email):
    if not '@' in email:
        return {'valid': False}

    if not '.' in email:
        return {'valid': False}

    return {'valid': True, 'email': email}

@login_required
def share_event(request):
    """
    View meant to share an event through Ajax request.

    The POST request needs to contain following keys:
    `val`: an email address where the event Invitation needs to be send
    `event_id`: the id of the event that is being shared throug email.

    The view response with a JSON containing following keys:
    `is_executed`: Boolean that tells whether the request was executed succesfully.
    `reason`: contains a error message meant to inform the `user` or the `programmer`
    of the corresponding error.
    """

    failure=__contains_failure(request, keys=['val'], only_owner=False)
    if failure:
        return failure

    event=Event.objects.get(pk=request.POST.get('event_id'))

    res=__is_valid_email(request.POST.get('val'))
    if not res.get('valid'):
        return JsonResponse({'is_executed': False, 'reason': 'unvalid email'})

    context={
            'user': request.user,
            'http_protocol': getHTTP_Protocol(),
            'domain': get_current_site(request).domain,
            'path': reverse("events:profile", kwargs={'event_id': event.pk}),
            }

    mail_subject=f"Invitation to {event.name}"
    mail_message_txt = render_to_string('events/messages/share_event.txt', context=context)

    email = EmailMessage(subject=mail_subject, body=mail_message_txt, to=[res.get('email')])
    email.send(fail_silently=True)

    return JsonResponse({'is_executed': True})

@require_http_methods(["POST"])
@login_required
@has_artist_profile
@is_band_owner
def update_location(request):
    """
    View meant to update the address and the corresponding, longitude and latitude of the event location through Ajax request.

    The POST request needs to contain following keys:
    `long`: the new longitude value
    `lat`: the new latitude value
    `address`: the human readable address
    `event_id`: the id of the event for which the address, longitude and latitude is being updated.

    The view response with a JSON containing following keys:
    `is_executed`: Boolean that tells whether the request was executed succesfully.
    `reason`: contains a error message meant to inform the `user` or the `programmer`
    of the corresponding error.
    """

    failure=__contains_failure(request, keys=['address', 'long', 'lat'])
    if failure:
        return failure

    event=Event.objects.get(pk=request.POST.get('event_id'))
    event.address=request.POST.get('address')
    event.longitude=request.POST.get('long')
    event.latitude=request.POST.get('lat')
    event.save()
    return JsonResponse({'is_executed': True})


@require_http_methods(["POST"])
@login_required
@has_artist_profile
@is_band_owner
def delete_event(request):
    """
    View that is called when a user desires to delete an event.
    The request is performed through Ajax.

    The POST request needs to contain following keys:
    `event_id`: the id of the event that needs to be deleted

    The view response with a JSON containing following keys:
    `is_executed`: Boolean that tells whether the request was executed succesfully.
    `reason`: contains a error message meant to inform the `user` or the `programmer`
    of the corresponding error.
    """
    failure=__contains_failure(request, keys=[], only_owner=True)
    if failure:
        return failure

    event=Event.objects.get(pk=request.POST.get('event_id'))
    event.delete()

    return JsonResponse({'is_executed': True})
