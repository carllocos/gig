from django.urls import path

from . import views


app_name = 'events'


urlpatterns = [
path("create/", views.create_event, name="create"),
path("profile/<int:event_id>", views.event_profile, name="profile"),

]
