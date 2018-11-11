from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from artists.artist_util import has_artist_profile, is_band_owner

from musicians.models import Band
from .forms import CreateEventForm
from .models import Event

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
            'is_owner': band.is_owner(request.user),
            'comments': event.get_comments(),
            'participants': event.get_participants(),
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
