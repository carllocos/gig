from django import forms
from .models import ArtistModel, ProfilePicModel, BackGroundPicModel


class CreateArtistForm(forms.ModelForm):

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

            self.cleaned_data['instruments'] = self.__instruments_to_str(dict)
            self.cleaned_data['genres'] = self.__genres_to_str(dict)
            self.cleaned_data['idols'] = self.__idols_to_str(dict)

            return True

        return False


    def save(self, user):

        art = ArtistModel(stage_name = self.cleaned_data['stage_name'],
                          instruments = self.cleaned_data['instruments'],
                          genres =  self.cleaned_data['genres'],
                          idols =  self.cleaned_data['idols'],
                          biography=self.cleaned_data['biography'],
                          user=user)

        art.save()

        #Creating and saving the profile/ background_pic model.
        profile_pic= self.cleaned_data.get('profile_pic', False)
        profil_pic_name = profile_pic.name if profile_pic else  ''
        pp_model = ProfilePicModel.createPic(artist=art, title=profil_pic_name)
        pp_model.save(profile_pic)

        bg_pic= self.cleaned_data.get('background_pic', False)
        bg_pic_name = bg_pic.name if bg_pic else  ''
        bp_model = BackGroundPicModel.createPic(artist=art, title=bg_pic_name)
        bp_model.save(bg_pic)

        return art

    def __instruments_to_str(self, dict):
        """
        The various instrument input fields int `dict` are transformed into one signle string.
        """
        return self.__inputs_to_single_str(dict,
                                            'instrument',
                                            self.__get_amount_instruments(dict))

    def __genres_to_str(self, dict):
        """
        The various genre input fields int `dict` are transformed into one signle string.
        """
        return self.__inputs_to_single_str(dict,
                                            'genre',
                                            self.__get_amount_genres(dict))

    def __idols_to_str(self, dict):
        """
        The various idol input fields int `dict` are transformed into one signle string.
        """
        return self.__inputs_to_single_str(dict,
                                            'idol',
                                            self.__get_amount_idols(dict))


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

    def __remove_comma(self, s):
        if len(s)<= 0:
            return ''
        if s.endswith(','):
            return self.__remove_comma(s[:-1])
        else:
            return s

    def __inputs_to_single_str(self, dict, input_prefix, amount):

        single_str=''
        for i in range(amount):
            input_key = f'{input_prefix}{i}'
            s = dict.get(input_key, '')
            if s != '' :
                single_str+= self.__remove_comma(s)

        return single_str
