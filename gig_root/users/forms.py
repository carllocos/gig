import json

from django import forms
from .models import User
from django.core.validators import MinLengthValidator, MaxLengthValidator

from .validators import lettersDigitsValidator




class RegistrationForm(forms.ModelForm):

    password = forms.CharField(widget=forms.PasswordInput, validators=[MinLengthValidator(8), MaxLengthValidator(32), lettersDigitsValidator])
    confirm_password = forms.CharField(widget=forms.PasswordInput,validators=[MinLengthValidator(8), MaxLengthValidator(32)])

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'password']

    def clean(self):
        cleaned_data = super(RegistrationForm, self).clean()
        confirm_password = cleaned_data.get('confirm_password')
        password = cleaned_data.get('password')

        if not password == confirm_password:
            self.add_error('confirm_password', 'Password does not match.')


class UserProfileForm(forms.Form):

    first_name = forms.CharField(required=True)
    last_name = forms.CharField(required=True)
    email = forms.EmailField(required=True)

    def is_valid(self, email):
        if super(UserProfileForm, self).is_valid():

            if email != self.cleaned_data.get('email', False):
                self.add_error('email', "Email can't change")
                return False

            return True

        else:
            if email != self.cleaned_data.get('email', False):
                self.add_error('email', "Email can't change")
            return False

    def errors_to_dict(self):
        if not self.errors:
            return {}


        error_json = json.loads(self.errors.as_json())

        dct = {
            'first_name': self._get_message(error_json, 'first_name'),
            'last_name': self._get_message(error_json, 'last_name'),
            'email': self._get_message(error_json, 'email'),
        }

        return dct

    def _get_message(self, error_json, key):
        msg_json = error_json.get(key, None)
        if msg_json is None:
            return ""
        else:
            return msg_json[0].get('message')
