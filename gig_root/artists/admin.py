from django.contrib import admin
from artists.models import ArtistModel, ProfilePic, BackgroundPic
# Register your models here.
admin.site.register(ArtistModel)
admin.site.register(ProfilePic)
admin.site.register(BackgroundPic)
