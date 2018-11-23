import os

from django.conf import settings

def getHTTP_Protocol():
    """
    function that returns `http://` or `https://`. Depending on which
    protocol is being used currently. 
    """
    if settings.DEBUG:
        return 'http://'
    else:
        return 'https://'
