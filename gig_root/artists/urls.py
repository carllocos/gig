from django.urls import path, include
from . import views


app_name='artists'

urlpatterns = [
    path('', views.home, name='home'),
    path('profile/<int:profile_id>/', views.view_profile, name='artist-profile'),
    path('register/', views.register_artist_view, name='register' ),
    path('register/ajax/', views.ajax_suggestions, name="suggest-ajax"),
    path('profile/update_genre_idol_instrument/', views.update_genre_idol_instrument, name="update-genres-idols-insts"),
    path('profile/update_stage_name/', views.update_stage_name, name="update-stage-name"),
    path('profile/update_biography/', views.update_biography, name="update-biography"),
]
