import os

from django.db.models.signals import pre_delete
from django.dispatch import receiver
from django.conf import  settings
from django.db import models

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
    def __init__(self, *args, **kwargs):
        super(ProfilePic, self).__init__(*args, **kwargs)


    def __str__(self):
        return f'Profile pic of band: {self.band.name}'

class BackgroundPic(PictureAbstract):
    def __init__(self, *args, **kwargs):
        super(BackgroundPic, self).__init__(*args, **kwargs)


    def __str__(self):
        return f'Background pic of band: {self.band.name}'


class Band(models.Model):

    MAX_LENGTH=100
    name = models.CharField(null=False, max_length=MAX_LENGTH)
    description =models.TextField(null=True, db_column="description")
    _genres =models.TextField(null=True, db_column="genres")
    owner = models.ForeignKey(ArtistModel, db_column="owner", on_delete=models.CASCADE, related_name="owns")
    profile_pic = models.OneToOneField(ProfilePic, db_column= "background_pic", default="", null=True, on_delete=models.SET_DEFAULT)#, related_name="background_of_band")
    background_pic = models.OneToOneField(BackgroundPic, db_column= "profile_pic", default="", null=True, on_delete=models.SET_DEFAULT)#, related_name="profile_of_band")
    # background_pic = models.OneToOneField(Picture, db_column= "background_pic", default="", null=True, on_delete=models.SET_DEFAULT, related_name="background_of_band")
    # profile_pic = models.OneToOneField(Picture, db_column= "profile_pic", default="", null=True, on_delete=models.SET_DEFAULT, related_name="profile_of_band")
    # band_pics = models.ForeignKey(BandPic, db_column="Band pictures", default="", null=True, on_delete=models.SET_DEFAULT, related_name="bandpic_of")
    # band_pics = models.ForeignKey(Picture, db_column="Band pictures", default="", null=True, on_delete=models.SET_DEFAULT, related_name="bandpic_of")

    #location attribute
    #videos=
    #social media associations:
    #main location of the band

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
        return self.owner.user.email

    def is_owner(self, other):
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
        return self.lineup.get_member(artist, only_active_members)

    def get_active_members(self, default=False):
        """
        Returns a Queryset of Member instances where the attribute `is_active` is equal to True.
        """
        return self.lineup.get_memberships()

    def is_member(self, other, only_active_members=True):
        return self.lineup.is_member(other, only_active_members)

    def add_member(self, artist, role="No role dessigned", is_active=False):
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

    def __str__(self):
        return f'Band Comment' + super(BandComment, self).__str__()

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
        return self.bandcommentvote_set.filter(voter=user).exits()


    def __vote(self, user, is_upvote):
        if self.already_voted(user):
            return False
        else:
            return self.bandcommentvote_set.create(voter=user, is_upvote)

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



class BandCommentVote(VoteAbstract):
    """
    Vote meant to represent the upvotes or downvotes towards one Comment of a band.
    """
    comment=models.ForeignKey(BandComment, on_delete=models.CASCADE)
    def __str__(self):
        v= 'upvote' if self.is_upvote else 'downvote'
        return f'{v} for comment {self.comment}'
