from django.contrib import admin
from .models import Band, Member, LineUp, ProfilePic, BackgroundPic, BandPic, VideoBand, BandComment, BandCommentVote

admin.site.register(Band)
admin.site.register(Member)
admin.site.register(LineUp)
admin.site.register(ProfilePic)
admin.site.register(BackgroundPic)
admin.site.register(BandPic)
admin.site.register(VideoBand)
admin.site.register(BandComment)
admin.site.register(BandCommentVote)
