from django import forms
from cloudinary.forms import CloudinaryJsFileField

from .models import ArtistModel, DEFAULT_PROFILE_PIC, DEFAULT_BACKGROUND_PIC, ProfilePic, BackgroundPic

class DirectUploadProfilePic(forms.Form):
    """
    Form to direcly upload a profile picture to cloudinary from client-side
    """
    profile_picture = CloudinaryJsFileField(attrs = { 'id': "id_new_profile_pic" })




class DirectUploadBackgroundPic(forms.Form):
    """
    Form to direcly upload a background picture to cloudinary from client-side
    """
    background_pic = CloudinaryJsFileField(attrs = { 'id': "id_new_background_pic" })

class CreateArtistForm(forms.ModelForm):
    """
    Form to create an artist profile.
    """

    stage_name = forms.CharField(required=False)

    profile_pic = forms.ImageField(required=False)
    background_pic = forms.ImageField(required=False)
    instruments = forms.CharField(required=False)
    genres =  forms.CharField(required=False)
    idols =  forms.CharField(required=False)

    biography = forms.CharField(required=False, widget=forms.Textarea)

    class Meta:
        model = ArtistModel
        fields = ['stage_name', 'biography']


    def __init__(self, *args, **kwargs):
        super(CreateArtistForm, self).__init__(*args, **kwargs)
        self.fields['instruments'].widget.attrs ={
                'id': 'id_instruments',
                'type': 'text',
                'class': 'instruments'
        }


        self.fields['genres'].widget.attrs ={
                'id': 'id_genres',
                'type': 'text',
                'class': 'genres'
        }

        self.fields['idols'].widget.attrs ={
                'id': 'id_idols',
                'type': 'text',
                'class': 'idols'
        }

    def is_valid(self, dict):
        if super(CreateArtistForm, self).is_valid():

            self.cleaned_data['instruments'] = self.__instruments_to_lst(dict)
            self.cleaned_data['genres'] = self.__genres_to_lst(dict)
            self.cleaned_data['idols'] = self.__idols_to_lst(dict)

            return True

        return False


    def save(self, user):

        art = ArtistModel(stage_name = self.cleaned_data['stage_name'],
                          instruments = self.cleaned_data['instruments'],
                          genres =  self.cleaned_data['genres'],
                          idols =  self.cleaned_data['idols'],
                          biography=self.cleaned_data['biography'],
                          user=user)

        #Creating and saving the profile/ background_pic model.
        profile_pic= self.cleaned_data.get('profile_pic', None)
        if profile_pic is None:
            profile_pic = DEFAULT_PROFILE_PIC
        art.profile_pic = ProfilePic().upload_and_save(profile_pic)

        bg_pic= self.cleaned_data.get('background_pic', None)
        if bg_pic is None:
            bg_pic=DEFAULT_BACKGROUND_PIC
        art.background_pic =  BackgroundPic().upload_and_save(bg_pic)

        art.save()

        return art

    def __instruments_to_lst(self, dict):
        """
        The various instrument input fields int `dict` are transformed into a list of strings.
        """
        return self.__inputs_to_lst(dict, 'instrument', self.__get_amount_instruments(dict))

    def __genres_to_lst(self, dict):
        """
        The various genres input fields int `dict` are transformed into a list of strings.
        """
        return self.__inputs_to_lst(dict, 'genre', self.__get_amount_genres(dict))

    def __idols_to_lst(self, dict):
        """
        The various idols input fields int `dict` are transformed into a list of strings.
        """
        return self.__inputs_to_lst(dict, 'idol', self.__get_amount_idols(dict))

    def __get_amount_instruments(self, dict):
        return self.__get_amount('amount_instruments', dict)

    def __get_amount_genres(self, dict):
        return self.__get_amount('amount_genres', dict)

    def __get_amount_idols(self, dict):
        return self.__get_amount('amount_idols', dict)


    def __get_amount(self, key, dict):
        val = dict.get(key, '')
        if val == '':
            return 0
        else:
            try:
                return int(float(val))
            except ValueError:
                return 0

    def __inputs_to_lst(self, dict, input_prefix, amount):
        return [dict.get(f'{input_prefix}{i}', '') for i in range(amount)]
