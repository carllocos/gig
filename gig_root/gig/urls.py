"""gig URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from . import views


app_name = 'gig_app'



urlpatterns = [
    path('', views.home, name='home'),
    path('admin/', admin.site.urls),
    path('search_suggestions/', views.search_suggestions, name='search-suggestions'),
    path('search/', views.search_query, name='search'),
    path('oauth/', include('social_django.urls', namespace='social')),
    path('artists/', include('artists.urls', namespace='artists')),
    path('musicians/', include('musicians.urls', namespace='musicians')),
    path('events/', include('events.urls', namespace='events')),
    path('users/', include('users.urls')),

]
