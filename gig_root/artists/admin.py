from django.contrib import admin
from artists.models import ArtistModel, Photo, ProfilePicModel, BackGroundPicModel
# Register your models here.
admin.site.register(ArtistModel)

admin.site.register(Photo)
admin.site.register(ProfilePicModel)
admin.site.register(BackGroundPicModel)
