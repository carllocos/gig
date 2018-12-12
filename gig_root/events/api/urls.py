from . import views
from django.urls import path, include, re_path

app_name='api-events'

urlpatterns = [
    path('', views.EventsListView.as_view(), name="events-retrieve"),
    re_path(r'^(?P<pk>\d+)/$', views.EventRUDView.as_view(), name='event-rud'),
]
