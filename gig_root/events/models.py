import os

from django.utils import timezone
from django.conf import settings
from django.db import models
from django.db.models.signals import pre_delete
from django.dispatch import receiver

from users.sharedModels import CommentAbstract, PictureAbstract, VoteAbstract
from users.models import User
from musicians.models import Band

DEFAULT_EVENT_PIC = path= os.path.join(settings.STATICFILES_DIRS [0], "pics/event_default.jpg")

def str_to_int(s , default=False):
    try:
        return int(float(s))
    except ValueError:
        return default

def str_to_float(s):
    return float(s)

class EventPicture(PictureAbstract):
    """
    Model that represents the picture from an event.
    """
    def __init__(self, *args, **kwargs):
        super(EventPicture, self).__init__(*args, **kwargs)


    def __str__(self):
        return f'Event picture of: {self.event.name}'



class Event(models.Model):
    """
    Event is a model that holds all the information of an upcoming gig for musicians.
    The name, date, some description, band that will play and so on.
    """
    MAX_LENGTH_NAME=70
    picture=models.OneToOneField(EventPicture, null=True, default="", on_delete=models.SET_DEFAULT)
    name=models.CharField(max_length=MAX_LENGTH_NAME, null=False)
    date=models.DateTimeField()
    band=models.ForeignKey(Band, on_delete=models.CASCADE)
    description=models.TextField(default="", null=True)

    #We store the latitude and longitude as location for the event.
    _latitude=models.FloatField(default=50.8503, null=False)
    _longitude=models.FloatField(default=4.3517, null=False)

    def __str__(self):
        return f'event {self.name} for {self.band.name}'

    @property
    def latitude(self):
        return self._latitude

    @property
    def longitude(self):
        return self._longitude

    @latitude.setter
    def latitude(self, lat):
        self._latitude=str_to_float(lat)

    @longitude.setter
    def longitude(self, long):
        self._longitude=str_to_float(long)


    def is_owner(self,user):
        """
        method that will check whether the user is the owner of this event.
        """
        if not user.is_authenticated:
            return False

        if not user.has_artistProfile():
            return False

        return self.band.owner == user.get_artist()

    def add_comment(self, msg, commentator):
        """
        add_comment method creates a EventComment instance with `msg` as the comment
        and `commentator` as a User instance that commented.

        Raises a ValueError if `msg` is an empty string or `commentator` is not a User
        instance
        """
        if msg == "":
            raise ValueError("`msg` cannot be an empty string")
        if not isinstance(commentator, User):
            raise ValueError("`commentator` has to be a `User` type")

        return self.eventcomment_set.create(comment=msg, commentator=commentator)

    def get_comment(self, comment_pk, default=False):
        """
        get_comment returns a comment with primary key equal to `pk`.
        If the comment don't exists `default` is returned
        """
        try:
            return self.eventcomment_set.get(pk=str_to_int(comment_pk))
        except:
            return default

    def get_comments(self):
        """
        returns a queryset of all comments ordered.
        """
        return self.eventcomment_set.all()

    def delete_comment(self, pk, default=False):
        """
        delete_comment removes band comment with primary key equal to `pk`.
        Returns True if operation went well. Otherwise `default` is returned
        """
        try:
            self.eventcomment_set.get(pk=pk).delete()
            return True
        except:
            return default

    def upvote(self, comment_pk, user):
        """
        `upvote` upvotes comment with primary key `comment_pk` where `user` is the voter.
        Returns the newly created vote instance or False.
        """
        c=self.get_comment(comment_pk)
        if not c:
            raise ValueError(f'No comment associated with primary key `{comment_pk}`')

        return c.upvote(user)

    def downvote(self, comment_pk, user):
        """
        `downvote` downvotes comment with primary key `comment_pk` where `user` is the voter.
        Returns the newly created vote instance or False.
        """
        c=self.get_comment(comment_pk)
        if not c:
            raise ValueError(f'No comment associated with primary key `{comment_pk}`')

        return c.downvote(user)


    def get_participant(self, user):
        """
        `get_participant` returns a Participant instance for `user`
        """
        if self.is_participant(user):
            return self.participant_set.get(participant=user)
        return False

    def get_participants(self):
        """
        `get_participants` returns a queryset of all Participants
        """
        return self.participant_set.all()

    def add_participant(self, user):
        """
        `add_participant` creates a Participant instance for `user`, if no one exists.
        """
        if not self.is_participant(user):
            return self.participant_set.create(participant=user)
        return False

    def remove_participant(self, user):
        """
        `remove_participant` removes a Participant instance associated with `user`
        """
        p=self.get_participant(user)
        if p:
            p.delete()
            return True
        return False

    def is_participant(self, user):
        """
        `is_participant` checks whether `user` is associated with a Participant instance.
        In other words, checks whether `user` indicated that he/she will participate to `self` event.
        """
        return user.is_authenticated and self.participant_set.filter(participant=user).exists()

    @property
    def amount_participants(self):
        return self.get_participants().count()

    @staticmethod
    def get_upcoming_events(events=None):
        now=timezone.now()
        if events is None:
            return Event.objects.filter(date__gte=now).order_by('date')
        else:
            return events.filter(date__gte=now).order_by('date')



@receiver(pre_delete, sender=Event)
def delete_pic(sender, instance, **kwargs):
    """
    This function will be called before an Event instance is deleted. To remove the associated pic of the event
    """
    EventPicture.delete_pics([instance.picture])



class EventComment(CommentAbstract):
    """
    Represents a comment associated to an event.
    """
    event = models.ForeignKey(Event, on_delete=models.CASCADE)


    @property
    def upvotes(self):
        """Get the amount of upvotes for this comment."""
        return  self.amount_upVotes()
    @property
    def downvotes(self):
        """Get the amount of downvotes for this comment."""
        return  self.amount_downVotes()

    def __str__(self):
        return f'Event Comment' + super(EventComment, self).__str__()

    def get_vote(self, voter, default=False):
        """
        get_vote returns a vote associated to `voter`. `voter` can be a string or int primary_key
        or a User instance. If no vote exists for `voter`, `default` is returned
        """
        if isinstance(voter, int) or isinstance(voter, str):
            try:
                return self.commentvote_set.get(pk=str_to_int(voter))
            except:
                return default
        elif isinstance(voter, User):
            try:
                return self.commentvote_set.get(voter=voter)
            except:
                return default
        else:
            raise TypeError("Wrong type for `voter`. Voter can only be a int, str representing a primary key. Or a User instance")

    def get_votes(self, only_up=None):
        """
        get_votes returns by default all votes for this comment.
        `only_up` set to true returns only upvotes. Set to false only downvotes
        """
        if only_up is None:
            return self.commentvote_set.all()
        if only_up:
            return self.commentvote_set.filter(is_upvote=True)
        else:
            return self.commentvote_set.filter(is_upvote=False)

    def amount_upVotes(self):
        """
        Returns the amount of upvotes for this comment
        """
        return self.commentvote_set.filter(is_upvote=True).count()

    def amount_downVotes(self):
        """
        Returns the amount of downvotes for this comment
        """
        return self.commentvote_set.filter(is_upvote=False).count()

    def already_voted(self, user):
        """
        already_voted checks whether `user` already voted this comment
        """
        return self.commentvote_set.filter(voter=user).exists()


    def __vote(self, user, is_upvote):
        if self.already_voted(user):
            return False
        else:
            return self.commentvote_set.create(voter=user, is_upvote=is_upvote)

    def upvote(self, user):
        """
        upvote will create a CommentVote instance with `is_upvote` set to True
        and `voter` set to `user`.

        This method calls `already_voted` first to ensure that the `user` didn't already
        vote. If the `user` already voted False is returned otherwise the new instance is returned.
        """
        return self.__vote(user, is_upvote=True)

    def downvote(self, user):
        """
        downvote will create a CommentVote instance with `is_upvote` set to False
        and `voter` set to `user`.

        This method calls `already_voted` first to ensure that the `user` didn't already
        vote. If the `user` already voted False is returned otherwise the new instance is returned.
        """
        return self.__vote(user, is_upvote=False)

    def inverse_vote(self, user):
        """
        inverse_vote will inverse the current vote of the `user`.
        E.g. `is_upvote` equal to True becomes False

        This method assumes that `already_voted` was called to ensure that the vote exists
        for the voter `user`.
        """
        v=self.commentvote_set.get(voter=user)
        v.is_upvote = not v.is_upvote
        v.save()



class CommentVote(VoteAbstract):
    """
    Vote meant to represent the upvotes or downvotes towards one Comment of an Event.
    """
    comment=models.ForeignKey(EventComment, on_delete=models.CASCADE)
    def __str__(self):
        v= 'upvote' if self.is_upvote else 'downvote'
        return f'{v} for {self.comment}'

class Participant(models.Model):
    """
    Model to represent the amount of Participants for one Event instance.
    """
    event=models.ForeignKey(Event, on_delete=models.CASCADE)
    participant = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return f'{self.participant.first_name} {self.participant.last_name} participates in {self.event.name}'
