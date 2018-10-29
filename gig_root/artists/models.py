from django.db import models
from users.models import User

class BandModel(models.Model):
    pass



#Represents the artistprofile of one user.
#The ArtistProfile is equivalen to a peron's C.V.
#The artist can afterwards be involved in multiple bands and solobands

class ArtistModel(models.Model):
    stage_name = models.CharField(max_length=30, null=True) # can be null

    #each gig user can have at most one artistprofile
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)

    profile_pic = models.CharField(max_length=50) ##This is a String of max x characters
    background_pic = models.CharField(max_length=50)

    biography = models.TextField(null=True)

    #Each artist can specify what he/she can play
    #e.g. guitar, voice,...
    instruments = models.TextField(null=True)

    #Favorit genres
    genres = models.TextField(null=True)

    #musicians that inspired the artist
    idols =  models.TextField(null=True)

    bands = models.ManyToManyField(BandModel)
