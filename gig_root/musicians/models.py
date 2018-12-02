import os

from django.utils import timezone
from django.db.models.signals import pre_delete
from django.dispatch import receiver
from django.conf import  settings
from django.db import models
from django.core.validators import URLValidator

from artists.models import ArtistModel
from users.models import User
from users.sharedModels import PictureAbstract, VideoAbstract, VoteAbstract, CommentAbstract

DEFAULT_BAND_PROFILE_PIC = path= os.path.join(settings.STATICFILES_DIRS [0], "pics/band_default_profile.png")
DEFAULT_BAND_BACKGROUND_PIC = path= os.path.join(settings.STATICFILES_DIRS [0], "pics/band_default_background.jpg")

def str_to_int(s , default=False):
    try:
        return int(float(s))
    except ValueError:
        return default


class ProfilePic(PictureAbstract):
    """
    Model that represents the profile picture of a band.
    """
    def __init__(self, *args, **kwargs):
        super(ProfilePic, self).__init__(*args, **kwargs)


    def __str__(self):
        return f'Profile pic of band: {self.band.name}'

class BackgroundPic(PictureAbstract):
    """
    Model tha represents the background picture of a band.
    """

    def __init__(self, *args, **kwargs):
        super(BackgroundPic, self).__init__(*args, **kwargs)


    def __str__(self):
        return f'Background pic of band: {self.band.name}'



class Band(models.Model):
    """
    Each `Band` instance corresponds with one band. Each band information such as
    a band name, description, genres that the band plays, and so on.
    Each band can also contain urls to other social profiles like soundcloud and youtube,
    which are used to display eventual playlist, video's of that band

    """

    MAX_LENGTH=100
    name = models.CharField(null=False, max_length=MAX_LENGTH)
    description =models.TextField(null=True, db_column="description")
    _genres =models.TextField(null=True, db_column="genres")
    owner = models.ForeignKey(ArtistModel, db_column="owner", on_delete=models.CASCADE, related_name="owns")
    profile_pic = models.OneToOneField(ProfilePic, db_column= "background_pic", default="", null=True, on_delete=models.SET_DEFAULT)
    background_pic = models.OneToOneField(BackgroundPic, db_column= "profile_pic", default="", null=True, on_delete=models.SET_DEFAULT)

    _soundcloud_profile_url = models.TextField(default='', null=True, validators=[URLValidator()])
    _soundcloud_playlist_url = models.TextField(default='', null=True)

    class Meta:
        verbose_name="Band Profile"
        verbose_name_plural="Bands Profiles"

    def save(self):
        self._genres = self.__set_to_str(self.genres)
        super(Band, self).save()

        try:
             self.lineup
        except:
            l=LineUp(band=self)
            l.save()
            self.lineup=l
            super(Band, self).save()

        return self


    def __str__(self):
        return self.name

    @staticmethod
    def get_band(pk, default=False):
        """
        Returns a band model based on the primary key `pk`.
        If the instance do not exists `default` is returned.
        `pk` can be either an integer or a string
        """
        if isinstance(pk, str):
            pk=str_to_int(pk)
            if not pk:
                return default
        else:
            if not isinstance(pk, int):
                return default
        try:
            return Band.objects.get(pk=pk)
        except:
            return default

    def get_contact_email(self):
        """
        Method that returns the email of the band owner.
        Whenever a user wants to contact the responsable of a band,
        this email is returned.
        """
        return self.owner.user.email

    def is_owner(self, other):
        """
        Method that checks wether `other` is the owner of this band profile.
        """
        if isinstance(other, ArtistModel):
            return self.owner == other
        elif isinstance(other, User):
            if other.is_authenticated:
                return self.owner == other.get_artist()
            else:
                return False
        else:
            return False

    def get_member(self, artist, only_active_members=True):
        """
        Method that returns a `Member` instance  corresponding to artist with profile `artist`.
        `only_active_members` if set to true returns only the instance if `artist` is currently active
        in the band.
        """
        return self.lineup.get_member(artist, only_active_members)

    def get_active_members(self, default=False):
        """
        Returns a Queryset of Member instances where the attribute `is_active` is equal to True.
        """
        return self.lineup.get_memberships()

    def is_member(self, other, only_active_members=True):
        """
        Method that checks whether `other` is a member of this band.
        """
        return self.lineup.is_member(other, only_active_members)

    def add_member(self, artist, role="No role dessigned", is_active=False):
        """
        Method that adds `artist` as a member of the band which active status set to `is_active`
        """
        return self.lineup.add_member(artist=artist, role=role, is_active=is_active)

    @property
    def genres(self):
        if isinstance(self._genres, str):
            self._genres = self.__str_to_set(self._genres)
        return self._genres

    @genres.setter
    def genres(self, val):
        """
        `val` has to be a list/set of string or a string
        """
        if isinstance(val, list):
            self._genres=set(val)
        elif isinstance(val, set):
            self._genres=val
        elif isinstance(val, str):
            self._genres=self.__str_to_set(self.__remove_comma(val))
        else:
            raise TypeError("input must be a String or a list/set of Strings")

    def add_genre(self, g):
        if g in self.genres:
            return False
        else:
            self.genres.add(g)
            return True

    def remove_genre(self, g):
        try:
            self.genres.remove(g)
            return True
        except KeyError:
            return False

    def get_video_set(self):
        return self.videoband_set.all()

    def add_comment(self, msg, commentator):
        """
        add_comment method creates a BandComment instance with `msg` as the comment
        and `commentator` as a User instance that commented.

        Raises a ValueError if `msg` is an empty string or `commentator` is not a User
        instance
        """
        if msg == "":
            raise ValueError("`msg` cannot be an empty string")
        if not isinstance(commentator, User):
            raise ValueError("`commentator` has to be a `User` type")

        return self.bandcomment_set.create(comment=msg, commentator=commentator)

    def get_comment(self, comment_pk, default=False):
        """
        get_comment returns a comment with primary key equal to `pk`.
        If the comment don't exists `default` is returned
        """
        try:
            return self.bandcomment_set.get(pk=str_to_int(comment_pk))
        except:
            return default

    def get_comments(self):
        """
        returns a queryset of all comments ordered.
        """
        return self.bandcomment_set.all()

    def delete_comment(self, pk, default=False):
        """
        delete_comment removes band comment with primary key equal to `pk`.
        Returns True if operation went well. Otherwise `default` is returned
        """
        try:
            self.bandcomment_set.get(pk=pk).delete()
            return True
        except:
            return default

    def upvote(self, comment_pk, user):
        """
        upvote upvotes comment with primary key `comment_pk` where `user` is the voter.
        Returns the newly created vote instance or False.
        """
        c=self.get_comment(comment_pk)
        if not c:
            raise ValueError(f'No comment associated with primary key `{comment_pk}`')

        return c.upvote(user)

    def downvote(self, comment_pk, user):
        """
        downvote downvotes comment with primary key `comment_pk` where `user` is the voter.
        Returns the newly created vote instance or False.
        """
        c=self.get_comment(comment_pk)
        if not c:
            raise ValueError(f'No comment associated with primary key `{comment_pk}`')

        return c.downvote(user)


    @property
    def upvotes(self):
        """Get the amount of upvotes for this band."""
        return  self.amount_upVotes()
    @property
    def downvotes(self):
        """Get the amount of downvotes for this band."""
        return  self.amount_downVotes()

    def get_vote(self, voter, default=False):
        """
        get_vote returns a vote associated to `voter`. `voter` can be a string or int primary_key
        or a User instance. If no vote exists for `voter`, `default` is returned
        """
        if isinstance(voter, int) or isinstance(voter, str):
            try:
                return self.bandprofilevote_set.get(pk=str_to_int(voter))
            except:
                return default
        elif isinstance(voter, User):
            try:
                return self.bandprofilevote_set.get(voter=voter)
            except:
                return default
        else:
            raise TypeError("Wrong type for `voter`. Voter can only be a int, str representing a primary key. Or a User instance")

    def get_votes(self, only_up=None, only_down=None):
        """
        get_votes returns by default all votes for this band.
        `only_up` set to true returns only upvotes. only_down set to True only downvotes
        """
        if only_up is None and only_down is None:
            return self.bandprofilevote_set.all()
        if only_up and only_down is None:
            return self.bandprofilevote_set.filter(is_upvote=True)
        elif only_down and only_up is None:
            return self.bandprofilevote_set.filter(is_upvote=False)
        else:
            return self.bandprofilevote_set.all()

    def amount_upVotes(self):
        """
        Returns the amount of upvotes for this band
        """
        return self.get_votes(only_up=True).count()

    def amount_downVotes(self):
        """
        Returns the amount of downvotes for this band
        """
        return self.get_votes(only_down=True).count()

    def already_voted(self, user):
        """
        already_voted checks whether `user` already voted for this band
        """
        return self.bandprofilevote_set.filter(voter=user).exists()


    def __vote(self, user, is_upvote):
        if self.already_voted(user):
            return False
        else:
            return self.bandprofilevote_set.create(voter=user, is_upvote=is_upvote)

    def upvote(self, user):
        """
        upvote will create a BandProfileVote instance with `is_upvote` set to True
        and `voter` set to `user`.

        This method calls `already_voted` first to ensure that the `user` didn't already
        vote. If the `user` already voted False is returned otherwise the new instance is returned.
        """
        return self.__vote(user, is_upvote=True)

    def downvote(self, user):
        """
        downvote will create a BandProfileVote instance with `is_upvote` set to False
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
        v=self.bandprofilevote_set.get(voter=user)
        v.is_upvote = not v.is_upvote
        v.save()

    def is_follower(self, user):
        """
        `is_follower` checks wether `user` is a follower of `self` instance
        """
        if not user.is_authenticated:
            return False

        return self.follow_set.filter(follower=user).exists()

    def add_follower(self, user):
        """
        `add_follower` marks `user` as follower of `self` band. The method calls first
        `is_follower` to check whether user is already a follower or not.
        Returns the `Follow` intance if the user is added otherwise False is returned
        """
        if self.is_follower(user):
            return False
        return self.follow_set.create(band=self, follower=user)

    def remove_follower(self, user):
        """
        Method that removes `user` from the follow_set. In other words the user indicated that he/she
        is no longer interested in this band.
        """
        if self.is_follower(user):
            return self.follow_set.get(follower=user).delete()
        return False

    def get_followers(self):
        """
        Returns the set of all followers of `self` band.
        """
        return self.follow_set.all()

    @property
    def amount_followers(self):
        """
        Method that returns the amount of followers for `self` band.
        """
        return self.follow_set.all().count()

    def get_upcoming_events(self):
        """
        Method that returns upcoming event instances associated to `self` band
        """
        now=timezone.now()
        return self.event_set.filter(date__gte=now)

    @property
    def soundcloud_profile_url(self):
        return self._soundcloud_profile_url

    @soundcloud_profile_url.setter
    def soundcloud_profile_url(self, url):
        if url == '':
            self._soundcloud_profile_url=False
        else:
            self._soundcloud_profile_url=url

    @property
    def soundcloud_playlist_url(self):
        return self._soundcloud_playlist_url

    @soundcloud_playlist_url.setter
    def soundcloud_playlist_url(self, url):
        if url == '':
            self._soundcloud_playlist_url=False
        else:
            self._soundcloud_playlist_url=url

    def __remove_comma(self, s):
        if len(s)<= 0:
            return ''
        if s.endswith(','):
            return self.__remove_comma(s[:-1])
        else:
            return s

    def __str_to_set(self, s):
        st=set()
        for e in s.split(','):
            if e !='':
                st.add(e)
        return st

    def __set_to_str(self, st):
        single_str=''
        for s in st:
            if not isinstance(s, str):
                raise TypeError("List/set must only contain String elements")

            s= self.__remove_comma(s)

            if s != '':
                single_str+= ',' + s

        return single_str




@receiver(pre_delete, sender=Band)
def delete_pics(sender, instance, **kwargs):
    """
    This function will be called before a band instance is deleted. To remove the associated pics of the band
    """
    ProfilePic.delete_pics([instance.profile_pic, instance.background_pic])


class BandPic(PictureAbstract):
    """
    Model that represents a picture of a band. Besides of a profile or background picture, a
    band can upload multiple pictures.
    """

    band=models.ForeignKey(Band, on_delete=models.CASCADE)

    def __init__(self, *args, **kwargs):
        super(BandPic, self).__init__(*args, **kwargs)


    def __str__(self):
        return f'Pic of band: {self.band.name}'



@receiver(pre_delete, sender=Band)
def delete_videos(sender, instance, **kwargs):
    """
    This function will be called before a band instance is deleted. To remove the associated videos of the band
    """
    VideoBand.delete_videos(instance.videoband_set.all())


class VideoBand(VideoAbstract):
    band=models.ForeignKey(Band, on_delete=models.CASCADE)

    def __init__(self, *args, **kwargs):
        super(VideoBand, self).__init__(*args, **kwargs)


    def __str__(self):
        return f'Video of band: {self.band.name}'


class LineUp(models.Model):
    """
    LineUp model represents a line up of a `band`. All members can be accessed through `members` attribute.
    """
    band=models.OneToOneField(Band, default="", on_delete=models.CASCADE)

    def __str__(self):
        return f'LineUp for band {self.band.name}'

    def add_member(self, artist, role, is_active):
        return self.member_set.create(artist=artist, role=role, is_active=is_active)

    def is_member(self, member, only_active_members= False):
        """
        This method tests whether `member` is part of this LineUp.
        `member` can be a User, AritstModel or a Member instance.
        """
        if isinstance(member, Member):
            m=self.member_set.filter(pk=member.pk)
        elif isinstance(member, User):
            if member.is_authenticated and member.has_artistProfile():
                m=self.member_set.filter(artist__pk=member.get_artist().pk)
            else:
                return False
        elif isinstance(member, ArtistModel):
            m=self.member_set.filter(artist__pk=member.pk)
        else:
            return False

        if m.exists():
            if only_active_members:
                return m.first().is_active
            return True
        else:
            return False


        if m.exits():
            if only_active_members:
                return m.is_active
            return True
        else:
            return False

    def get_memberships(self, only_active_members=True):
        """
        Returns all Member instances from the member_set where `is_active`== `only_active_members`
        """
        return self.member_set.filter(is_active=only_active_members)


    def get_member(self, artist, only_active_members=True):
        """
        Returns a Member instance associated to artist from the member_set. If `only_active_members` is
        set to true, the Member instance is returned only if it's active
        """
        try:
            m=self.member_set.get(artist__pk=artist.pk)
            if only_active_members and m.is_active:
                return m
            return m
        except:
            return False



class Member(models.Model):
    """
    Member model represents the `role` of an `aritst` in a particular band. The artist can whether be
    active or inactive depending on the value of `is_active`.
    """
    role= models.CharField(max_length=100, null=False, default="")
    artist=models.ForeignKey(ArtistModel, on_delete=models.CASCADE, default="", null=True, related_name="line_ups")
    is_active=models.BooleanField(default=False)
    lineup=models.ForeignKey(LineUp, default="", null=False, on_delete=models.CASCADE)

    def __str__(self):
        return f'{self.artist.get_stage_name()} with role {self.role}'

    def get_band(self):
        return self.lineup.band

    @staticmethod
    def get_member(pk, default=False):
        """
        Returns a LineUpMember instance based on the primary key `pk`.
        If the instance do not exists `default` is returned.
        `pk` can be either an integer or a string
        """
        if isinstance(pk, str):
            pk=str_to_int(pk)
            if not isinstance(pk, int):
                return default
        else:
            if not isinstance(pk, int):
                return default
        try:
            return Member.objects.get(pk=pk)
        except:
            return default


class BandComment(CommentAbstract):
    """
    Represents a comment associated to a band.
    """
    band = models.ForeignKey(Band, on_delete=models.CASCADE)


    @property
    def upvotes(self):
        """Get the amount of upvotes for this comment."""
        return  self.amount_upVotes()
    @property
    def downvotes(self):
        """Get the amount of downvotes for this comment."""
        return  self.amount_downVotes()

    def __str__(self):
        return f'Band Comment' + super(BandComment, self).__str__()

    def get_vote(self, voter, default=False):
        """
        get_vote returns a vote associated to `voter`. `voter` can be a string or int primary_key
        or a User instance. If no vote exists for `voter`, `default` is returned
        """
        if isinstance(voter, int) or isinstance(voter, str):
            try:
                return self.bandcommentvote_set.get(pk=str_to_int(voter))
            except:
                return default
        elif isinstance(voter, User):
            try:
                return self.bandcommentvote_set.get(voter=voter)
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
            return self.bandcommentvote_set.all()
        if only_up:
            return self.bandcommentvote_set.filter(is_upvote=True)
        else:
            return self.bandcommentvote_set.filter(is_upvote=False)

    def amount_upVotes(self):
        """
        Returns the amount of upvotes for this comment
        """
        return self.bandcommentvote_set.filter(is_upvote=True).count()

    def amount_downVotes(self):
        """
        Returns the amount of downvotes for this comment
        """
        return self.bandcommentvote_set.filter(is_upvote=False).count()

    def already_voted(self, user):
        """
        already_voted checks whether `user` already voted this comment
        """
        return self.bandcommentvote_set.filter(voter=user).exists()


    def __vote(self, user, is_upvote):
        if self.already_voted(user):
            return False
        else:
            return self.bandcommentvote_set.create(voter=user, is_upvote=is_upvote)

    def upvote(self, user):
        """
        upvote will create a BandCommentVote instance with `is_upvote` set to True
        and `voter` set to `user`.

        This method calls `already_voted` first to ensure that the `user` didn't already
        vote. If the `user` already voted False is returned otherwise the new instance is returned.
        """
        return self.__vote(user, is_upvote=True)

    def downvote(self, user):
        """
        downvote will create a BandCommentVote instance with `is_upvote` set to False
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
        v=self.bandcommentvote_set.get(voter=user)
        v.is_upvote = not v.is_upvote
        v.save()

class Follow(models.Model):
    """
    Model to represent the follower of one band instance.
    """
    band=models.ForeignKey(Band, on_delete=models.CASCADE)
    follower = models.ForeignKey(User, on_delete=models.CASCADE)

    class Meta:
        db_table= "followers"

    def __str__(self):
        return f'{self.follower.get_full_name()} follows {self.band.name}'

class BandCommentVote(VoteAbstract):
    """
    Vote meant to represent the upvotes or downvotes towards one Comment of a band.
    """
    comment=models.ForeignKey(BandComment, on_delete=models.CASCADE)
    def __str__(self):
        v= 'upvote' if self.is_upvote else 'downvote'
        return f'{v} for comment {self.comment}'


class BandProfileVote(VoteAbstract):
    """
    This model represents a vote towards one Band profile
    """
    band = models.ForeignKey(Band, on_delete=models.CASCADE)

    def __str__(self):
        v= 'upvote' if self.is_upvote else 'downvote'
        return f'{v} for band {self.band}'
