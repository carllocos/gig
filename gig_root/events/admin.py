from django.contrib import admin
from . import models

admin.site.register(models.Event)
admin.site.register(models.EventComment)
admin.site.register(models.CommentVote)
admin.site.register(models.EventPicture)
