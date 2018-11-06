from django.urls import path

from . import views

app_name='musicians'
urlpatterns =[
    path('', views.test),
    path('register/', views.register_band, name='band-register'),
    path('profile/<int:profile_id>', views.band_profile, name="band-profile"),
    path('update_description/', views.update_description, name="update-description"),
    path('update_genre/', views.update_genre, name="update-genre"),
    path('update_linup/', views.update_line_up, name='update-line-up'),
    path('add_member/', views.add_member, name='add-member'),
    path('confirm_member/<int:line_up_id>', views.confirm_member, name='confirm-membership'),

]
