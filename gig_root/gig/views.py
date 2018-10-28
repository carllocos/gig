from django.shortcuts import render
from django.http import HttpResponse
from django.urls import reverse

#TODO Needs to be removed
from django.contrib.auth.decorators import login_required

#@login_required
def home(request):
    return render(request, "gig/home.html", {'user': request.user})
