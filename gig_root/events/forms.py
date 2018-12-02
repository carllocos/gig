import json

from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from cloudinary.forms import CloudinaryJsFileField

from django import forms
from musicians.models import Band
from .models import Event, EventPicture, DEFAULT_EVENT_PIC


class DirectUploadPic(forms.Form):
    """
    Form to directly upload a picture to cloudinary from the client-side.
    """
    picture = CloudinaryJsFileField(attrs = { 'id': "id_new_picture" },
                                    label="",
                                    )

class DateInput(forms.DateInput):
    """
    DateInput Field meant to check validity of a new date value, when the user attempts
    to update the date of an existing event.
    """
    input_type= 'date'

class TimeInput(forms.TimeInput):
    """
    TimeInput Field meant to check validity of a new time value, when the user attempts
    to update the time of an existing event.
    """
    input_type='time'

class CreateEventForm(forms.ModelForm):
    """
    Form provided that allows a user to create an upcoming event for one of his/her bands.
    """

    band=forms.ModelChoiceField(queryset=Band.objects.none(),
                                help_text='Chose the band for which this event is meant',
                                to_field_name="name",
                                empty_label="Chose a band",
                                error_messages={'required': "You need to chose a band",'invalid_choice': "Invalid choice"})

    picture=forms.ImageField(required=False, help_text="Event Picture")

    date= forms.DateField(widget=DateInput(), help_text='Date of the event')

    time =forms.TimeField(widget=TimeInput(),
                          required=True,
                          label="Time",
                          help_text="start time of event",
                          )

    class Meta:
        model= Event

        exclude=('date', 'band', 'picture')
        help_texts={
            'name' : ('Add a short clear name'),
            'description': ('Tell people more about the event'),
        }

    def __init__(self, *args, **kwargs):
        qs=kwargs.pop('bands')
        super(CreateEventForm, self).__init__(*args, **kwargs)
        self.fields['band'].queryset=qs
        self.fields['description'].required = False


    def clean_date(self):
        """
        clean_date makes sure that the chosen date is not in the past.
        """
        date=self.cleaned_data['date']
        if date < timezone.now().date():
            raise forms.ValidationError(
                    _('The date cannot be in the past.'),
                        code='invalid')
        return date


    def save(self, *args, **kwargs):
        now=timezone.now()
        d=self.cleaned_data.get('date')
        t=self.cleaned_data.get('time')
        dt=timezone.datetime(d.year, d.month, d.day, t.hour, t.minute, t.second, t.microsecond,now.tzinfo)
        self.cleaned_data['date']=dt
        self.instance.date = self.cleaned_data['date']
        self.instance.band = self.cleaned_data['band']
        super(CreateEventForm, self).save(*args, **kwargs)

    def savePicture(self):
        """
        Method called seperatly from `self.save`, to save a picture into cloudinary.
        """

        pic=self.cleaned_data.get('picture', None)
        if pic is None:
            pic=DEFAULT_EVENT_PIC
        event_picture=EventPicture(event=self.instance).upload_and_save(pic)

        self.instance.picture=event_picture
