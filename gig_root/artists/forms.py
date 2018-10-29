
from django import forms
from .models import ArtistModel


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
                          profile_pic = 'profile_pic',
                          background_pic = 'background_pic',
                          instruments = self.cleaned_data['instruments'],
                          genres =  self.cleaned_data['genres'],
                          idols =  self.cleaned_data['idols'],
                          biography=self.cleaned_data['biography'],
                          user=user
                          )
        art.save()
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
            # if dict.get(key, None) is None:
            #     return ""

        result=""
        for i in range(amount):
            input_key = f'{input_prefix}{i}'
            val = dict.get(input_key, None)
            if val is not None and val != '' :
                result += f',{val}'
        return result
