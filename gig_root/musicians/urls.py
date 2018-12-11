from django.urls import path, re_path

from . import views

app_name='musicians'
urlpatterns =[
    path('register/', views.register_band, name='band-register'),
    path('delete/', views.delete_profile, name='band-delete'),
    path('agenda/<int:band_id>', views.agenda, name='agenda'),
    path('profile/<int:profile_id>', views.band_profile, name="band-profile"),
    path('update_description/', views.update_description, name="update-description"),
    path('update_genre/', views.update_genre, name="update-genre"),
    path('update_member/', views.update_member, name='update-member'),
    path('add_member/', views.add_member, name='add-member'),
    re_path(r'^confirm_member/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/(?P<mid64>[0-9A-Za-z_\-]+)/$',
        views.confirm_member, name='confirm-membership'),
    path('update_picture/', views.update_picture, name='update-picture'),
    path('update_video/', views.update_video, name='update-video'),
    path('add_comment/', views.add_comment, name='add-comment'),
    path('vote_comment/', views.vote_comment, name="vote-comment"),
    path('vote_band/', views.vote_band, name="vote-band"),
    path('update_follow/', views.update_follow, name="update-follow"),
    path('update_soundcloud/', views.update_soundcloud_url, name="update-soundcloud"),
    path('update_youtube/', views.update_youtube_url, name="update-youtube"),

]
