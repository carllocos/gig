import requests

from social_core.backends.facebook import FacebookOAuth2
from social_core.pipeline.partial import partial
from django.urls import reverse
from django.shortcuts import redirect


from users.models import User

def create_fail():
    return

def retrieve_user(strategy, details, user=None, backend= None, *args, **kwargs):
    if user is None:

        us= User.get_user(details.get('email'))
        if us:
            return {'user': us}


@partial
def request_password(strategy, details, user=None, backend= None, *args, **kwargs):

    if user is None:
        local_password = strategy.session.get('local_password', None)
        if not local_password:
            #if not local password we request the user to chose a password
            strategy.session['user_data'] = details
            current_partial = kwargs.get('current_partial')

            query_string = '?partial_token={0}'.format(current_partial.token)
            return strategy.redirect(reverse('users:request-password') + query_string)

        return {'user_password': local_password}




def create_user(details, user=None,*args, **kwargs):

    if user is None:
        user = User.get_user(details.get('email'))
        if not user:

            user = User.objects.create_user(email=details.get('email'),
                                            first_name=details.get('first_name'),
                                            last_name=details.get('last_name'),
                                            password=kwargs.get('user_password'))
            user.save()

        return {'user': user}
    return


def _facebook_request(**kwargs):

    fbuid = kwargs['response']['id']
    access_token= kwargs['response']['access_token']

    request_url = 'https://graph.facebook.com/{0}/?fields=email&access_token={1}'.format(fbuid, access_token)
    resp = requests.get(request_url)

    return resp.json().get('email', False)


def retrieve_email(strategy, details, is_new, user=None , *args, **kwargs):

    if user and user.email:
        return
    elif is_new and not details.get('email'):
        if strategy.request_data().get('email'):
            details['email']=strategy.request_data().get('email')
            return details

        if strategy.session.get('email','') != '':
            details['email']=strategy.session.get('email')
            return details

        backend = kwargs['backend']

        email_address = False
        if backend.name == FacebookOAuth2.name:
            email_address = _facebook_request(**kwargs)

        if email_address:
            details['email']=email_address
            return details
        else:
            ##TODO ADD THE case that we have to request the user for email or maybe find an alternative to register with email or somenthing else
            return
