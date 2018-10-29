from .base_settings import *


DEBUG=False
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_SSL_REDIRECT = True

SOCIAL_AUTH_REDIRECT_IS_HTTPS = True

# Honor the 'X-Forwarded-Proto' header for request.is_secure()
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')



# Database
# https://docs.djangoproject.com/en/2.1/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': env_config.get('PROD_DATABASE_ENGINE'),
        'NAME': env_config.get('PROD_DATABASE_NAME'),
        'USER':env_config.get('PROD_DATABASE_USER'),
        'PASSWORD': env_config.get('PROD_DATABASE_PASSWORD'),
        'HOST': env_config.get('PROD_DATABASE_HOST'),
    }
}
