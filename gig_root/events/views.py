import datetime
import json

from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from artists.artist_util import has_artist_profile, is_band_owner

from musicians.models import Band
from .forms import CreateEventForm, DirectUploadPic
from .models import Event, str_to_int

def event_profile(request, event_id):
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

    if not event.is_owner(request.user):
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
        datetime_obj = datetime.datetime.strptime(date_str, format_str).date()
    except:
        return {'valid': False, 'reason': 'new date has incorrect format.'}


    if datetime_obj < datetime.date.today():
        return {'valid': False, 'reason': 'date cannot be in the past.'}

    return {'valid': True, 'date': datetime_obj}

@require_http_methods(["POST"])
@login_required
@has_artist_profile
@is_band_owner
def update_date(request):
    failure=__contains_failure(request, keys=['val'])
    if failure:
        return failure

    event=Event.objects.get(pk=request.POST.get('event_id'))
    date=request.POST.get('val')
    valid= __is_valid_date(date)
    if not valid.get('valid'):
        return JsonResponse({'is_executed': False, 'reason': valid.get('reason')})

    d=valid.get('date')

    dt=datetime.datetime(d.year, d.month, d.day, event.date.hour, event.date.minute, event.date.second, event.date.microsecond, event.date.tzinfo)
    event.date=dt
    event.save()
    return JsonResponse({'is_executed': True})


def __is_valid_time(time_str, current_date):
    """
    private function to validate event time provided trough ajax request.
    """
    try:
        time=datetime.datetime.strptime(time_str, '%H:%M').time()
    except:
        return {'valid': False, 'reason': 'new date has incorrect format.'}

    now = datetime.datetime.now()
    new_d= datetime.datetime(current_date.year, current_date.month, current_date.day, time.hour, time.minute, time.second, time.microsecond, time.tzinfo)
    if new_d < now:
         return {'valid': False, 'reason': f'time and date cannot be in the past. Given {new_d}'}

    return {'valid': True, 'time': time}

@require_http_methods(["POST"])
@login_required
@has_artist_profile
@is_band_owner
def update_time(request):
    failure=__contains_failure(request, keys=['val'])
    if failure:
        return failure

    event=Event.objects.get(pk=request.POST.get('event_id'))
    time=request.POST.get('val')
    valid= __is_valid_time(time, event.date)
    if not valid.get('valid'):
        return JsonResponse({'is_executed': False, 'reason': valid.get('reason')})

    t=valid.get('time')
    dt=datetime.datetime(event.date.year, event.date.month, event.date.day, t.hour, t.minute, t.second, t.microsecond, t.tzinfo)
    event.date=dt
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
    failure=__contains_failure(request, keys=['val'])
    if failure:
        return failure

    event=Event.objects.get(pk=request.POST.get('event_id'))
    msg=request.POST.get('val')

    event.add_comment(msg, commentator=request.user)
    return JsonResponse({'is_executed': True})

@require_http_methods(["POST"])
@login_required
def vote_comment(request):
    failure=__contains_failure(request, keys=['val'], allowed_operations=['upvote', 'downvote'])
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
    failure=__contains_failure(request, keys=[], allowed_operations=['participate', 'disengage'])
    if failure:
        return failure

    operation=request.POST.get('operation')
    event=Event.objects.get(pk=request.POST.get('event_id'))

    if operation == 'participate':
        event.add_participant(request.user)
    else: #downvote
        event.remove_participant(request.user)

    return JsonResponse({'is_executed': True, 'participants': event.amount_participants})
