from django.utils import timezone

from rest_framework import generics

from events.models import Event
from .serializers import EventSerializer
from .permissions import IsOwnerEvent


class EventRUDView(generics.RetrieveUpdateDestroyAPIView):
    lookup_field = 'pk'
    queryset = Event.objects.all()
    serializer_class = EventSerializer
    permission_classes=[IsOwnerEvent]

    def get_queryset(self):
        return Event.objects.all()

    def get_object(self):
        pk=self.kwargs.get('pk')
        return Event.objects.get(pk=pk)


class EventsListView(generics.ListAPIView):
    queryset = Event.objects.all()
    serializer_class = EventSerializer

    def get_queryset(self):
        query=self.request.GET.get("query", '')
        if query is not '':
            return Event.objects.filter(name__icontains=query).distinct()

        # now=timezone.now()
        # return Event.objects.filter(date__gte=now).order_by('date')
        return Event.objects.order_by('date')

    def get_object(self):
        pk=self.kwargs.get('pk')
        return Event.objects.get(pk=pk)
