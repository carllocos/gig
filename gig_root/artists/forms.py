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
        amount_inst=self._get_amount('amount_instruments', dict)
        amount_genres=self._get_amount('amount_genres', dict)
        amount_idols=self._get_amount('amount_idols', dict)

        self.instruments = self._fetch_inputs(dict, '', 'instrument', amount_inst)
        self.genres = self._fetch_inputs(dict, '', 'genre', amount_genres)
        self.idols = self._fetch_inputs(dict, '', 'idol', amount_idols)

        return super(CreateArtistForm, self).is_valid()


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


    def _get_amount(self, key, dict):
        val = dict.get(key, '')
        if val == '':
            return 0
        else:
            try:
                return int(float(val))
            except ValueError:
                return 0

    def _fetch_inputs(self, dict, key, input_prefix, amount):
        result=""
        for i in range(amount):
            input_key = f'{input_prefix}{i}'
            val = dict.get(input_key, None)
            if val is not None and val != '' :
                result += f',{val}'
        return result
