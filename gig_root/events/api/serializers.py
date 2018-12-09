from django.utils import timezone

from rest_framework import serializers

from events.models import Event, EventPicture
from musicians.models import Band

class EventPictureSerializer(serializers.ModelSerializer):
    class Meta:
        model= EventPicture
        fields=[
            'title',
            'public_id',
            'width',
            'height',
        ]

from pprint import pprint
class EventSerializer(serializers.ModelSerializer):
    # picture=EventPictureSerializer()
    class Meta:
        model= Event
        fields=[
            'pk',
            'picture',
            'name',
            'date',
            'band',
            'description',
            'latitude',
            'longitude'
        ]

        read_only_fields=['pk', 'picture']


    def validate_band(self, band):
        request=self.context.get('request')
        user=request.user
        if not band.is_owner(user):
            raise serializers.ValidationError("You can't create any event for this band. You need to be the owner.")

        return band

    def validate_date(self, datetime):
        now=timezone.now()
        if datetime < now:
            raise serializers.ValidationError("The date and time can't be in the past")

        return datetime
