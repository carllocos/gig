from django.contrib import admin

from users.models import User
from users.sharedModels import Comment, Vote, Video

admin.site.register(User)
admin.site.register(Comment)
admin.site.register(Video)
admin.site.register(Vote)
