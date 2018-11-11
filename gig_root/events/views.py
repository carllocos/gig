from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from artists.artist_util import has_artist_profile, is_band_owner

from musicians.models import Band
from .forms import CreateEventForm

@require_http_methods(["GET", "POST"])
@login_required
@has_artist_profile
@is_band_owner
def create_event(request):

    artist=request.user.get_artist()
    bands=artist.owns.all()

    if request.method == 'POST':
        print(f"Request type {request.FILES.items()}")
        f=CreateEventForm(request.POST, request.FILES, bands=bands)
        if f.is_valid():
            f.save(commit=False)
            f.savePicture()
            f.instance.save()
            return redirect('events:profile', event_id=f.instance.pk)

        return render(request, "events/create.html",{'form': f})


    f=CreateEventForm(bands=bands)
    return render(request, "events/create.html",{'form': f})
