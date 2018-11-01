from django.urls import path, include
from . import views


app_name='artists'

urlpatterns = [
    path('', views.home, name='home'),
    path('profile/<int:profile_id>/', views.view_profile, name='artist-profile'),
    path('register/', views.register_artist_view, name='register' ),
    path('register/ajax/', views.ajax_suggestions, name="suggest-ajax"),
]
