from django.urls import path, re_path

from . import views

app_name='musicians'
urlpatterns =[
    path('', views.test),
    path('register/', views.register_band, name='band-register'),
    path('profile/<int:profile_id>', views.band_profile, name="band-profile"),
    path('update_description/', views.update_description, name="update-description"),
    path('update_genre/', views.update_genre, name="update-genre"),
    path('update_member/', views.update_member, name='update-member'),
    path('add_member/', views.add_member, name='add-member'),
    re_path(r'^confirm_member/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/(?P<mid64>[0-9A-Za-z_\-]+)/$',
        views.confirm_member, name='confirm-membership'),
    path('update_picture/', views.update_picture, name='update-picture'),
    path('update_video/', views.update_video, name='update-video'),

]
