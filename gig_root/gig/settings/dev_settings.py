from .base_settings import *

DEBUG=True
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
SECURE_SSL_REDIRECT = False
# Database
# https://docs.djangoproject.com/en/2.1/ref/settings/#databases
ALLOWED_HOSTS += ['localhost']
DATABASES = {
    'default': {
        'ENGINE': env_config.get('DEV_DATABASE_ENGINE', ''),
        'NAME': env_config.get('DEV_DATABASE_NAME', ''),
        'USER':env_config.get('DEV_DATABASE_USER', ''),
        'PASSWORD': env_config.get('DEV_DATABASE_PASSWORD', ''),
        'HOST': env_config.get('DEV_DATABASE_HOST', ''),
    }
}
