from django.contrib import admin

from users.models import User
from users.sharedModels import Comment, Vote

admin.site.register(User)
admin.site.register(Comment)
admin.site.register(Vote)
