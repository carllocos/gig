from django.contrib import admin
from . import models

admin.site.register(models.Band)
admin.site.register(models.Member)
admin.site.register(models.LineUp)
admin.site.register(models.ProfilePic)
admin.site.register(models.BackgroundPic)
admin.site.register(models.BandPic)
admin.site.register(models.VideoBand)
admin.site.register(models.BandComment)
admin.site.register(models.BandCommentVote)
admin.site.register(models.Follow)
