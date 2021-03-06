from django.urls import path

from . import views


app_name = 'events'


urlpatterns = [
path("create/", views.create_event, name="create"),
path('delete/', views.delete_event, name='delete'),
path("profile/<int:event_id>", views.event_profile, name="profile"),
path("details/<int:event_id>", views.event_details, name="details"),
path("edit/<int:event_id>", views.event_edit, name="edit"),
path("edit/update_name", views.update_name, name="update-name"),
path("edit/update_description", views.update_description, name="update-description"),
path("edit/update_date", views.update_date, name="update-date"),
path("edit/update_time", views.update_time, name="update-time"),
path("edit/update_band", views.update_band, name="update-band"),
path("edit/update_picture", views.update_picture, name="update-picture"),
path("add_comment/", views.add_comment, name="add-comment"),
path("vote_comment/", views.vote_comment, name="vote-comment"),
path("update_participation/", views.update_participation, name="update-participation"),
path("share_event/", views.share_event, name="share-event"),
path('update_location', views.update_location,name='update-location'),
]
