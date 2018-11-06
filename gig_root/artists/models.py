import os

import cloudinary
from django.db.models.signals import pre_delete
from django.dispatch import receiver
from django.conf import  settings
from django.db import models
from users.models import User

__path_to_default_pics = os.path.join(settings.STATICFILES_DIRS [0], "pics")

class ArtistModel(models.Model):
    """
    The ArtistModel represents an the profile of an artistself.
    The artist profile is equivalent to a person's C.V.
    Each instance of ArtistModel can be associated with different Band Profiles
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

    def get_active_bands(self):
        """
        Returns a Queryset of Linups where the artist is active in that bandself.
        The `is_active` attribute of an LineUpMember instance is set to True
        """
        return self.linups.filter(is_active=True)

    def save(self):
        self._instruments = self.__set_to_str(self.instruments)
        self._idols = self.__set_to_str(self.idols)
        self._genres = self.__set_to_str(self.genres)
        return super(ArtistModel, self).save()

    def is_owner(self, other):
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
        return self.profilepicmodel.public_id

    def get_background_pic_id(self):
        """
        Returns the `public_id` associated to the background picture of the artist.
        The public_id is needed to retrieve the background picture from the external web service
        `Cloudianry`
        """
        return self.backgroundpicmodel.public_id



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
    This function will be called before an ArtistProfile instance is deleted. To remove pics from Cloudinary
    """
    pp=instance.profilepicmodel
    bp=instance.backgroundpicmodel
    try:
        cloudinary.api.delete_resources([pp.public_id, bp.public_id])
    except:
        pass


import datetime

class Photo(models.Model):
    """
    Photo is a parent model for `ProfilePicModel` and `BackGroundPicModel`.
    Photo follows the `Template method pattern`, where the detials are left over to the subclasses.
    """
    __MAX_LENGTH = 200
    title = models.CharField(default="", max_length=__MAX_LENGTH, null=False)

    ## Points to a Cloudinary image
    public_id = models.CharField(default="", max_length=__MAX_LENGTH, null=False)

    @staticmethod
    def __remove_extension(img_description):
        return os.path.splitext(img_description)[0]

    @staticmethod
    def __correct_size(str_val):
        if len(str_val) > Photo.__MAX_LENGTH:
            str_val= str_val[0 : Photo.__MAX_LENGTH]
        return str_val

    @staticmethod
    def correct_img_title(title):
        no_ext=Photo.__remove_extension(title)
        return Photo.__correct_size(no_ext)

    @staticmethod
    def generate_random_key(description, artist):
        time_now = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        time_now2 = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        return Photo.__correct_size(str(artist.pk) + time_now + time_now2 + description)

    """ Informative name for model """
    def __unicode__(self):
        try:
            public_id = self.public_id
        except AttributeError:
            public_id = ''
        return "Photo <%s:%s>" % (self.title, public_id)


    def save(self, pic, pic_title, pic_path):
        """
        `save` method will save the `pic` into web service `Cloudinary`.
        And save the `ProfilePicModel` or `BackGroundPicModel`.
        If pic is false a default picture will be fetched from the `pic_path` and used instead.
        """
        if pic:
            metadata=cloudinary.uploader.upload(pic)
        else:
            metadata=cloudinary.uploader.upload(pic_path)

        if metadata.get('public_id', False):
            self.public_id = metadata.get('public_id')
        else:
            self.public_id= Photo.generate_random_key(pic_title, self.artist)
        return super(Photo, self).save()


class ProfilePicModel(Photo):
    """
    ProfilePicModel represents the profile picture of an Artist.
    A one-to-one relation is defined between both instancesself.
    """
    artist= models.OneToOneField(ArtistModel, on_delete=models.CASCADE, primary_key=True)

    class Meta:
        verbose_name = 'Profile Picture'
        verbose_name_plural = 'Profile Pictures'

    def __str__(self):
        try:
            public_id = self.public_id
        except AttributeError:
            public_id = ''

        eq = self.artist.stage_name == ''
        art = self.artist.user.first_name if  eq else self.artist.stage_name
        return "Profile Picture of %s <%s:%s>" % (art, self.title, public_id)


    def save(self, pic):
        """
        `save` method will save the ProfilePicModel instace through a super call and pass the given `pic` picture to it's parent class.
        """
        path= os.path.join(settings.STATICFILES_DIRS [0], "pics/profile_default.jpg")
        return super(ProfilePicModel, self).save(pic, "profile_pic", path)

    @staticmethod
    def createPic(artist, title="default Profile Pic"):
        """
        `createPic` static method will create an instance of the `ProfilePicModel` but not save it yet.
        """
        if title == '':
            title = "default Profile Pic"

        return ProfilePicModel(title=title, artist=artist)

class BackGroundPicModel(Photo):
    """
    BackGroundPicModel represents the background picture of an Artist.
    A one-to-one relation is defined between both instancesself.
    """

    artist= models.OneToOneField(ArtistModel, on_delete=models.CASCADE, primary_key=True)

    class Meta:
        verbose_name = 'Background Picture'
        verbose_name_plural = 'Background Pictures'

    def __str__(self):
        try:
            public_id = self.public_id
        except AttributeError:
            public_id = ''

        eq = self.artist.stage_name == ''
        art = self.artist.user.first_name if  eq else self.artist.stage_name
        return "Background Picture of %s <%s:%s>" % (art, self.title, public_id)

    def save(self, pic):
        """
        `save` method will save the BackGroundPicModel instace through a super call and pass the given `pic` picture to it's parent class.
        """
        path= os.path.join(settings.STATICFILES_DIRS [0], "pics/background_default.jpg")
        return super(BackGroundPicModel, self).save(pic, "background_pic", path)

    @staticmethod
    def createPic(artist, title="default Background Pic"):
        """
        `createPic` static method will create an instance of the `BackGroundPicModel` but not save it yet.
        """
        if title == '':
            title = "default Background Pic"

        return BackGroundPicModel(title=title, artist=artist)
