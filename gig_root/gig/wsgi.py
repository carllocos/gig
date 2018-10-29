"""
WSGI config for gig project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/2.1/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application
from decouple import Config, RepositoryEnv

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

#Reference to the file gig_root/gig/settings/'.env'
env_config = Config(RepositoryEnv(os.path.join(BASE_DIR, '.env')))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', env_config.get('DJANGO_SETTINGS_MODULE', 'gig.settings.prod_settings'))

application = get_wsgi_application()
