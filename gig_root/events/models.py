import os

from django.conf import settings
from django.db import models
from django.db.models.signals import pre_delete
from django.dispatch import receiver
from users.sharedModels import CommentAbstract, PictureAbstract, VoteAbstract
from musicians.models import Band

DEFAULT_EVENT_PIC = path= os.path.join(settings.STATICFILES_DIRS [0], "pics/event_default.jpg")

class EventPicture(PictureAbstract):
    def __init__(self, *args, **kwargs):
        super(EventPicture, self).__init__(*args, **kwargs)


    def __str__(self):
        return f'Event picture of: {self.event.name}'



class Event(models.Model):
    MAX_LENGTH_NAME=70
    picture=models.OneToOneField(EventPicture, null=True, default="", on_delete=models.SET_DEFAULT)
    name=models.CharField(max_length=MAX_LENGTH_NAME, null=False)
    date=models.DateTimeField()
    band=models.ForeignKey(Band, on_delete=models.CASCADE)
    description=models.TextField(default="", null=True)


    # location

    def __str__(self):
        return f'event {self.name} for {self.band.name}'

@receiver(pre_delete, sender=Event)
def delete_pic(sender, instance, **kwargs):
    """
    This function will be called before an Event instance is deleted. To remove the associated pic of the event
    """
    print("Im back here")
    EventPicture.delete_pics([instance.picture])



class EventComment(CommentAbstract):
    pass

class CommentVote(VoteAbstract):
    pass
