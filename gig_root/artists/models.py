import os
import cloudinary

from django.conf import  settings
from django.db import models
from users.models import User

__path_to_default_pics = os.path.join(settings.STATICFILES_DIRS [0], "pics")

class BandModel(models.Model):
    pass

class ArtistModel(models.Model):
    """
    The ArtistModel represents an the profile of an artistself.
    The artist profile is equivalent to a person's C.V.
    Each instance of ArtistModel can be associated with different Band Profiles
    """
    stage_name = models.CharField(max_length=30, null=True) # can be null

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

    bands = models.ManyToManyField(BandModel)

    class Meta:
        verbose_name = 'Artist Profile'
        verbose_name_plural = 'Artist Profiles'

    def __str__(self):
        if self.stage_name != '':
            return f'{self.stage_name}'
        else:
            return f'{self.user.first_name} {self.user.last_name}'


    @property
    def instruments(self):
        if isinstance(self._instruments, str):
            self._instruments = self.__str_to_lst(self._instruments)

        return self._instruments

    @instruments.setter
    def instruments(self, val):
        """
        `val` has to be a list of string or a string
        """
        if isinstance(val, list):
            self._instruments=self.__lst_to_str(val)
        elif isinstance(val, str):
            self._instruments=self.__remove_comma(val)
        else:
            raise TypeError("input must be a String or a list of Strings")

    @property
    def genres(self):
        if isinstance(self._genres, str):
            self._genres = self.__str_to_lst(self._genres)

        return self._genres

    @genres.setter
    def genres(self, val):
        """
        `val` has to be a list of string or a string
        """
        if isinstance(val, list):
            self._genres=self.__lst_to_str(val)
        elif isinstance(val, str):
            self._genres=self.__remove_comma(val)
        else:
            raise TypeError("input must be a String or a list of Strings")

    @property
    def idols(self):
        if isinstance(self._idols, str):
            self._idols = self.__str_to_lst(self._idols)

        return self._idols

    @idols.setter
    def idols(self, val):
        """
        `val` has to be a list of string or a string
        """
        if isinstance(val, list):
            self._idols=self.__lst_to_str(val)
        elif isinstance(val, str):
            self._idols=self.__remove_comma(val)
        else:
            raise TypeError("input must be a String or a list of Strings")

    @staticmethod
    def get_artist(pk, default=False):
        """
        Returns an artist model based on the primate key `pk`.
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

    def __str_to_lst(self, s):
        lst=[]
        for e in s.split(','):
            if e !='':
                lst.append(e)
        return lst

    def __lst_to_str(self, lst):
        single_str=''
        for s in lst:
            if not isinstance(s, str):
                raise TypeError("List must only contain String elements")

            s= self.__remove_comma(s)

            if s == '':
                continue
            if single_str == '':
                single_str+= s
            else:
                single_str+= ',' + self.__remove_comma(s)

        return single_str


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
