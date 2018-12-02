import os

import cloudinary
from django.db.models.signals import pre_delete
from django.dispatch import receiver
from django.conf import  settings
from django.db import models
from users.models import User
from users.sharedModels import PictureAbstract


DEFAULT_PROFILE_PIC = os.path.join(settings.STATICFILES_DIRS [0], "pics/profile_default.jpg")
DEFAULT_BACKGROUND_PIC = os.path.join(settings.STATICFILES_DIRS [0], "pics/background_default.jpg")

class ProfilePic(PictureAbstract):
    def __init__(self, *args, **kwargs):
        super(ProfilePic, self).__init__(*args, **kwargs)


    def __str__(self):
        return f'Profile pic of artist: {self.artistmodel.stage_name}'

class BackgroundPic(PictureAbstract):
    def __init__(self, *args, **kwargs):
        super(BackgroundPic, self).__init__(*args, **kwargs)


    def __str__(self):
        return f'Background pic of artist: {self.artistmodel.stage_name}'

class ArtistModel(models.Model):
    """
    The ArtistModel represents the profile of an artist. Information such as `stage_name`,
    `biography`, pictures, `instruments` that the artist can play, and so on.
    The artist profile is equivalent to a muscian's C.V.
    Each instance of ArtistModel can be associated with different Band Profiles,
    but only with one User.
    """

    MAX_LENGTH=30
    stage_name = models.CharField(max_length=MAX_LENGTH, null=True) # can be null

    #each gig user can have at most one artistprofile
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)

    biography = models.TextField(null=True)

    #Each artist can specify what he/she can play
    #e.g. guitar, voice,...
    _instruments = models.TextField(null=True, db_column="instruments")

    #Favorit genres
    _genres = models.TextField(null=True, db_column="genres")

    #musicians that inspired the artist
    _idols =  models.TextField(null=True, db_column="idols")

    profile_pic = models.OneToOneField(ProfilePic, db_column= "profile_pic", default="", null=True, on_delete=models.SET_DEFAULT)
    background_pic = models.OneToOneField(BackgroundPic, db_column= "background_pic", default="", null=True, on_delete=models.SET_DEFAULT)

    class Meta:
        verbose_name = 'Artist Profile'
        verbose_name_plural = 'Artist Profiles'

    def __str__(self):
        return self.get_stage_name()

    def get_stage_name(self):
        if self.stage_name != '':
            return f'{self.stage_name}'
        else:
            return f'{self.user.first_name} {self.user.last_name}'

    def get_memberships(self):
        """
        Returns a Queryset of `Member` instances where the artist belongs to. And the aritst is currently active in that band.
        The `is_active` attribute of an `Member` instance is set to True
        """
        return self.line_ups.filter(is_active=True)

    def save(self):
        self._instruments = self.__set_to_str(self.instruments)
        self._idols = self.__set_to_str(self.idols)
        self._genres = self.__set_to_str(self.genres)
        return super(ArtistModel, self).save()

    def is_owner(self, other):
        """
        Method that checks whether `other` is the owner of this artist profile
        """
        if isinstance(other, ArtistModel):
            return self.pk == other.get_artist().pk
        elif isinstance(other, User):
            if other.is_authenticated and other.has_artistProfile():
                return self.pk == other.get_artist().pk
            else:
                return False
        else:
            raise TypeError("`other` arguments needs to be of the type AritstModel or User Model")
        is_owner = user.is_authenticated and user.has_artistProfile() and user.get_artist().pk == profile_id

    @property
    def instruments(self):
        if isinstance(self._instruments, str):
            self._instruments = self.__str_to_set(self._instruments)

        return self._instruments

    @instruments.setter
    def instruments(self, val):
        """
        `val` has to be a list/set of string or a string
        """
        if isinstance(val, list):
            self._instruments=set(val)
        elif isinstance(val, set):
            self._instruments=val
        elif isinstance(val, str):
            self._instruments=self.__str_to_set(self.__remove_comma(val))
        else:
            raise TypeError("input must be a String or a list/set of Strings")

    def add_instrument(self, inst):
        if inst in self.instruments:
            return False
        else:
            self.instruments.add(inst)
            return True

    def remove_instrument(self, inst):
        try:
            self.instruments.remove(inst)
            return True
        except KeyError:
            return False

    def amount_instruments(self):
        return self.instruments.len()

    @property
    def genres(self):
        if isinstance(self._genres, str):
            self._genres = self.__str_to_set(self._genres)

        return self._genres

    @genres.setter
    def genres(self, val):
        """
        `val` has to be a list/set  of string or a string
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

    def amount_genres(self):
        return self.genres.len()

    @property
    def idols(self):
        if isinstance(self._idols, str):
            self._idols = self.__str_to_set(self._idols)

        return self._idols

    @idols.setter
    def idols(self, val):
        """
        `val` has to be a list/set of string or a string
        """
        if isinstance(val, list):
            self._idols=set(val)
        elif isinstance(val, set):
            self._idols=val
        elif isinstance(val, str):
            self._idols=self.__str_to_set(self.__remove_comma(val))
        else:
            raise TypeError("input must be a String or a list/set of Strings")

    def add_idol(self, i):
        if i in self.idols:
            return False
        else:
            self.idols.add(i)
            return True

    def remove_idol(self, i):
        try:
            self.idols.remove(i)
            return True
        except KeyError:
            return False

    def amount_idols(self):
        return self.idols.len()

    @staticmethod
    def get_artist(pk, default=False):
        """
        Returns an artist model based on the primary key `pk`.
        If the instance do not exists `default` is returned.
        """

        try:
            return ArtistModel.objects.get(pk=pk)
        except:
            return default

    def get_profile_pic_id(self):
        """
        Returns the `public_id` associated to the profile picture of the artist.
        The public_id is needed to retrieve the profile picture from the external web service
        `Cloudianry`
        """
        return self.profile_pic.public_id

    def get_background_pic_id(self):
        """
        Returns the `public_id` associated to the background picture of the artist.
        The public_id is needed to retrieve the background picture from the external web service
        `Cloudianry`
        """
        return self.background_pic.public_id

    def is_involved_with_bands(self):
        """
        Method that tells whether `self` artist is the owner or member of at least one band.
        """
        return self.owns.all().exists() or self.get_memberships().exists()

    def get_bands(self):
        """
        Method that returns a list of all bands where `self` artist is a member of.
        """

        bands=[]
        for membs in self.get_memberships():
            bands.append(membs.get_band())
        return bands

    def has_events(self):
        """
        Method that checks wether `self` artist created at least one event for a band that he/she owns.
        """
        bands=self.owns.all()
        if not bands.exists():
            return False

        for band in bands:
            if band.event_set.all().exists():
                return True

        #No event found
        return False

    def get_events(self):
        """
        Method that returns a list of all the events of bands for which the artist owns the band.
        """
        bands=self.owns.all()

        events_qs= False
        for band in bands:
            if isinstance(events_qs, bool):
                events_qs=band.event_set.all()
            else:
                events_qs=events_qs.union(band.event_set.all())

        events=[]
        for event in events_qs.order_by('-date'):
            events.append(event)

        return events

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


@receiver(pre_delete, sender=ArtistModel)
def delete_pics(sender, instance, **kwargs):
    """
    This function will be called before an ArtistProfile instance is deleted. To ensure that the associated profile and background pic get's deleted.
    """
    ProfilePic.delete_pics([instance.profile_pic, instance.background_pic])
