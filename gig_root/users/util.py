import os

from django.conf import settings

def getHTTP_Protocol():
    if settings.DEBUG:
        return 'http://'
    else:
        return 'https://'
