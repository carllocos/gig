import os

from django.db.models.signals import pre_delete
from django.dispatch import receiver
from django.conf import  settings
from django.db import models

from artists.models import ArtistModel
from users.models import User

import cloudinary


def defaultBandProfilePic():
    path= os.path.join(settings.STATICFILES_DIRS [0], "pics/band_default_profile.png")
    return Picture(title="profile_default_pic", default_pic=path)

def defaultBandBackgroundPic():
    path= os.path.join(settings.STATICFILES_DIRS [0], "pics/band_default_profile.jpg")
    return Picture(title="background_default_pic", default_pic=path)

def str_to_int(s , default=False):
    try:
        return int(float(s))
    except ValueError:
        return default

class Picture(models.Model):
    MAX_LENGTH=200

    title=models.CharField(default="", max_length=MAX_LENGTH, null=False)
    public_id=models.CharField(max_length=MAX_LENGTH, null=False)
    width = models.PositiveIntegerField(null=False)
    height = models.PositiveIntegerField(null=False)

    def __init__(self, *args, **kwargs):
        default_pic = kwargs.pop('default_pic', None)
        super(Picture, self).__init__(*args, **kwargs)
        if default_pic is not None:
            self.__pic=default_pic

    def __str__(self):
        return self.title

    def save(self, pic=None):
        """
        Save method will save the picture to Cloudinary
        """
        if not pic:
            pic=self.__pic
        metadata=cloudinary.uploader.upload(pic)
        self.height=metadata.get('height')
        self.width=metadata.get('width')
        self.public_id=metadata.get('public_id')
        if self.title.endswith(metadata.get('format')):
                new_title = self.title[:-len(metadata.get('format'))]
                self.title=new_title

        super(Picture, self).save()

    # def delete(self, *args, **kwargs):
    #     try:
    #         cloudinary.api.delete_resources([self.public_id])
    #
    #     except:
    #         pass
    #
    #     super(Picture, self).delete(*args, **kwargs)

class Video(models.Model):
    pass

class Vote(models.Model):
    #the vote can be replaced by just an integerfield
    #The vote can be done on a Artist and band profile but also on a comment
    pass

class Comment(models.Model):
    pass
    ##Comment belongs to band profile but also eventself.
    #cotnains a field of votes


class Band(models.Model):

    MAX_LENGTH=100
    name = models.CharField(null=False, max_length=MAX_LENGTH)
    description =models.TextField(null=True, db_column="description")

    #location attribute

    _genres =models.TextField(null=True, db_column="genres")

    owner = models.ForeignKey(ArtistModel, db_column="owner", on_delete=models.CASCADE, related_name="owns")
    background_pic = models.OneToOneField(Picture, db_column= "background_pic", default=None, null=True, on_delete=models.SET_DEFAULT, related_name="background_of")
    profile_pic = models.OneToOneField(Picture, db_column= "profile_pic", default=None, null=True, on_delete=models.SET_DEFAULT, related_name="profile_of")

    band_pics = models.ForeignKey(Picture, db_column="Band pictures", default=None, null=True, on_delete=models.SET_DEFAULT, related_name="bandpic_of")
    #videos=
    #social media associations:
    #main location of the band

    class Meta:
        verbose_name="Band Profile"
        verbose_name_plural="Bands Profiles"

    def save(self):
        self._genres = self.__set_to_str(self.genres)
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

    def get_line_up(self, artist):
        """
        Returns a LineUpMember instance belonging to `artist`.
        This method assumes that the instance exits
        """
        for l in self.linupmember_set.all():
            if l.member == artist:
                return l

    def get_active_members(self, default=False):
        """
        Returns a Queryset of LinupMember instances where the attribute `is_active` is equal to True.
        """
        return self.linupmember_set.filter(is_active=True)

    def is_member(self, other, only_active_members=True):
        """
        `is_member` method will test whether `other` is member of the band.
        `only_active_members` set on true tests additionally whether the member is an active member (`is_active` attribute is true).
        """
        if isinstance(other, ArtistModel):
            for l in self.linupmember_set.all():
                if l.artist.pk == other.pk:
                    if only_active_members:
                        return l.is_active
                    else:
                        return True

            return False
        elif isinstance(other, User):
            if other.is_authenticated and other.has_artistProfile():
                ar=other.get_artist()
                for l in self.linupmember_set.all():
                    if l.member.pk == ar.pk:
                        if only_active_members:
                            return l.is_active
                        else:
                            return True
                return False
            else:
                return False
        else:
            return False
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
    This function will be called before a band instance is deleted. To remove pics from Cloudinary
    """
    pp=instance.profile_pic
    bp=instance.background_pic
    try:
        cloudinary.api.delete_resources([pp.public_id, bp.public_id])
    except:
        pass

    pp.delete()
    bp.delete()




class LinupMember(models.Model):
    role= models.CharField(max_length=100, null=False, default="")
    member=models.ForeignKey(ArtistModel, on_delete=models.CASCADE, default="", null=True, related_name="linups")
    band= models.ForeignKey(Band, default="", on_delete=models.CASCADE)# related_name="linup_member")
    is_active=models.BooleanField(default=False)

    def __str__(self):
        return f'{self.member.get_stage_name()} with role {self.role} in band {self.band.name}'

    @staticmethod
    def get_line_up(pk, default=False):
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
            return LinupMember.objects.get(pk=pk)
        except:
            return default
