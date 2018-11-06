from django import forms

from .models import Band, Picture, defaultBandProfilePic, defaultBandBackgroundPic

class RegisterForm(forms.ModelForm):

    genres =  forms.CharField(required=False)
    background_pic = forms.ImageField(required=False)
    profile_pic = forms.ImageField(required=False)

    class Meta:
        model = Band
        fields=['name', 'description']


    def is_valid(self):
        if super(RegisterForm, self).is_valid():
            #TODO add error messages when genres is not valid: the amount of genres characteres is greater than the MAX_LENGTH allowed
            return self.__is_genres_valid()
        return False

    def save(self, artist):
        """
        Saving the associated band of this form and linking an artist to the band.
        """

        b=Band(name=self.cleaned_data['name'],
               description=self.cleaned_data['description'],
               genres=self.__genres_to_set(),
               owner=artist)

        #we create profile and background pic for the band instance
        profile_pic=self.cleaned_data.get('profile_pic', False)
        if profile_pic:
            pp_m=Picture(title=profile_pic.name)
            pp_m.save(profile_pic)
            b.profile_pic=pp_m
        else:
            bp_m=defaultBandProfilePic()
            bp_m.save()
            b.profile_pic=bp_m



        background_pic=self.cleaned_data.get('background_pic', False)
        if background_pic:
            bp_m=Picture(title=background_pic.name)
            bp_m.save(background_pic)
            b.background_pic=bp_m
        else:
            bp_m=defaultBandBackgroundPic()
            bp_m.save()
            b.background_pic=bp_m

        b.save()

        return b


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
