from django import forms
from cloudinary.forms import CloudinaryJsFileField

from .models import Band, LineUp, Member, DEFAULT_BAND_PROFILE_PIC, DEFAULT_BAND_BACKGROUND_PIC, ProfilePic, BackgroundPic

class URLForm(forms.Form):
    """
    Form to validate any url
    """
    url = forms.URLField(required=True, error_messages={'required': "You need to provida an url",'invalid': "The specified url is invalid"})

class SoundCloudURL(URLForm):
    """
    Form to validate a soundcloud profile url
    """
    soundcloud_prefix='https://soundcloud.com/'

    def is_valid(self):
        if super(SoundCloudURL, self).is_valid():
            url=self.cleaned_data['url']
            if not url.startswith(self.soundcloud_prefix):
                self.add_error('url', 'it is not a valid soundcloud url.')
                return False

            profile_name= url[len(self.soundcloud_prefix):]
            if profile_name == '':
                self.add_error('url', 'it is not a valid soundcloud url.')
                return False

            return True
        return False

class SoundCloudPlayListURL(SoundCloudURL):
    """
    Form to validate a soundcloud url of a playlist
    """

    soundcloud_prefix='https://w.soundcloud.com/player/'

    def is_valid(self):
        if super(SoundCloudURL, self).is_valid():
            return True

        return False

class DirectUploadProfilePicBand(forms.Form):
    """
    Form that allows client-side upload of a band profile picture.
    """
    profile_picture = CloudinaryJsFileField(attrs = { 'id': "id_new_band_profile_pic" })

class DirectUploadBackgroundPicBand(forms.Form):
    """
    Form that allows client-side upload of a band background picture.
    """
    background_pic = CloudinaryJsFileField(attrs = { 'id': "id_new_band_background_pic" })

class DirectUploadBandPic(forms.Form):
    """
    Form that allows client-side upload for a picture (no profile or background).
    """
    band_pic = CloudinaryJsFileField(attrs = { 'id': "id_new_band_pic" })

class DirectVideoUpload(forms.Form):
    """
    Form that allows client-side upload of a video for a band.
    """
    video = CloudinaryJsFileField(attrs = { 'id': "id_new_video" })

class RegisterForm(forms.ModelForm):
    """
    Form to register a band.
    """

    genres =  forms.CharField(required=False)
    background_pic = forms.ImageField(required=False)
    profile_pic = forms.ImageField(required=False)

    class Meta:
        model = Band
        fields=['name', 'description']


    def is_valid(self):
        if super(RegisterForm, self).is_valid():
            return self.__is_genres_valid()
        return False

    def save(self, artist):
        """
        Creates and saves a Band instance, profile- and background Picture instances based on the cleaned_data.
        The pictures are uploaded and saved through call to `upload_and_save` method.
        Additionally a LineUp instance is created for this band.
        """

        band=Band(name=self.cleaned_data['name'],
               description=self.cleaned_data['description'],
               genres=self.__genres_to_set(),
               owner=artist)

        #we create profile and background pic for the band instance
        profile_pic=self.cleaned_data.get('profile_pic', None)
        if profile_pic is None:
            profile_pic=DEFAULT_BAND_PROFILE_PIC
        band.profile_pic=ProfilePic(band=band).upload_and_save(profile_pic)

        background_pic=self.cleaned_data.get('background_pic', None)
        if background_pic is None:
            background_pic=DEFAULT_BAND_BACKGROUND_PIC
        band.background_pic=BackgroundPic(band=band).upload_and_save(background_pic)

        band.save()
        return band


    def __is_genres_valid(self):
        """
        Validator to check whether all provided genres together are not longer
        than MAX_LENGTH chars
        """
        l=0
        for i in range(self.__get_amount()):
            l+=len(self.data.get(f'genre{i}', ''))
            if l > Band.MAX_LENGTH:
                return False

        if l > Band.MAX_LENGTH:
            return False
        else:
            return True

    def __genres_to_set(self):
        s=set()
        for i in range(self.__get_amount()):
            g=self.__clean_genre(self.data.get(f'genre{i}',''))
            if g:
                s.add(g)
        return s

    def __clean_genre(self, genre):
        if genre =='':
            return False
        else:
            return genre

    def __get_amount(self):
        val = self.data.get('amount_genres', '')
        if val == '':
            return 0
        else:
            try:
                return int(float(val))
            except ValueError:
                return 0
