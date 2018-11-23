from django.contrib.sites.shortcuts import get_current_site
from django.contrib.auth import views as auth_view
from django.contrib.auth.decorators import login_required
from django.contrib import auth as authentication
from django.core.mail import EmailMessage
from django.http import HttpResponse, JsonResponse, HttpResponseBadRequest
from django.urls import reverse
from django.shortcuts import redirect, render
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.utils.encoding import force_bytes, force_text
from django.views.generic import CreateView
from django.template.loader import render_to_string

from social_django.utils import load_strategy

from .forms import RegistrationForm, UserProfileForm, EmailChangeForm
from .models import User
from .tokens import account_activation_token
from .util import getHTTP_Protocol


@login_required
def update_email(request):
    """
    View that is called when a user desires to update it's current email.
    In the corresponding post request the user is expected to provide it's
    current password, as security mechanism, and the new email address.
    A confirmation link is send to the new email address as additional validity.
    """
    form = EmailChangeForm(user=request.user, data=request.POST or None)
    if request.POST and form.is_valid():
        context ={
                'user':request.user,
                'http_protocol': getHTTP_Protocol(),
                'domain': get_current_site(request).domain,
                'token': account_activation_token.make_token(request.user),
                'uid': urlsafe_base64_encode(force_bytes(request.user.pk)).decode(),
                'eid64': urlsafe_base64_encode(force_bytes(form.cleaned_data['email'])).decode(),
                }

        mail_subject = 'Email Update confirm'
        mail_message_txt = render_to_string('users/messages/update_email.txt', context=context)

        emailMsg = EmailMessage(subject=mail_subject, body=mail_message_txt, to=[form.cleaned_data['email']])
        emailMsg.send(fail_silently=True)

        context_msg= {
            'title_page': 'Email update',
            'title_msg': 'Confirmation Email Send',
            'short_message': 'A confirmation email was send. To confirm email change click on the link send to the new email address.',
        }
        return render(request, 'users/short_message.html', context=context_msg)

    return render(request, 'users/update_email.html', {'form': form})

@login_required
def update_email_confirm(request, uidb64, token, eid64):
    """
    View that is called when the user confirms the email change by clicking on the confirmation link received
    throug email.
    """
    try:
        uid = force_text(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
        email=force_text(urlsafe_base64_decode(eid64))
    except(TypeError, ValueError, OverflowError, User.DoesNotExist):
        user=None
        email=None

    if user is None or email is None or not account_activation_token.check_token(user, token):
        context= {'short_message': "You seem to have an invalid link. Check if you are logged in with a correct profile. Remember to use previous email to confirm email update.",
                  'title_msg': "Invalid activation link",
                  'title_page': "Bad request"}
        return render(request, 'users/short_message.html',context=context)

    if user.pk != request.user.pk:
        context= {'short_message': "You are trying to perform a request not meant for you. Check if you are logged in with a correct profile.",
                  'title_msg': "Unauhtorized request",
                  'title_page': "Bad request"}
        return render(request, 'users/short_message.html',context=context)

    user.email=email
    user.save()
    context= {'short_message': f"Your email was succesfuly changed to {email}",
              'title_msg': "Email change completed",
              'title_page': f"Email update completed",
              }
    return render(request, 'users/short_message.html',context=context)


def request_password(request):
    """
    View that invites the user to complete and confirm data, after a user
    choses to signup through third party apps (e.g. facebook or gmail).
    `RegistrationForm` will ask the user to chose a password for further logins
    """
    partial_token=request.GET.get('partial_token')

    if request.method == 'GET':
        user_details = request.session.get('user_data')

        kwown_data = {
            'first_name': user_details.get('first_name'),
            'last_name': user_details.get('last_name'),
            'email': user_details.get('email')
        }
        form = RegistrationForm(initial=kwown_data)
        return render(request, 'users/social_account_form.html', {'form': form})
    else:
        form = RegistrationForm(request.POST)
        if form.is_valid():
            strategy = load_strategy()
            partial = strategy.partial_load(request.GET.get('partial_token'))

            session = request.session
            session['local_password'] = form.cleaned_data.get('password')
            backend_name = session.get('backend_name')
            return redirect(reverse('social:complete', kwargs={'backend': partial.backend}))
        else:
            return render(request, 'users/social_account_form.html', {'form': form})


def confirm_account(request):
    """
    View that invites the user to confirm registration through email confirmation.
    """
    context= {
        'title_page': 'Signup Confirmation',
        'title_msg': 'Confirmation Email Send',
        'short_message': 'To complete the registration click on the link send to the email',
        'classes': '',
    }
    return  render(request, 'users/short_message.html', context=context)

def activate_account(request, uidb64, token):
    """
    View that activates the registration of a user, once the user clicks on the confirmation link received
    through email.
    """
    try:
        uid = force_text(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except(TypeError, ValueError, OverflowError, User.DoesNotExist):
        user=None
    if user is not None and account_activation_token.check_token(user, token):
        user.is_active=True
        user.save()

        authentication.login(request=request, user=user, backend='django.contrib.auth.backends.ModelBackend')

        return redirect(reverse('home'))
    else:
        return HttpResponse('Activation link is invalid!')


class SignupView(CreateView):
    """
    View that provides the user with a SignupForm and sends a confirmation link to the email of the user,
    once the form is filled correctly.
    """
    form_class = RegistrationForm
    success_url = 'users:signup-confirm'
    model = User
    template_name = 'users/signup.html'

    def form_valid(self, form):

        user_inst = form.save(commit=False)
        user_inst.set_password(form.cleaned_data.get('password'))
        user_inst.is_active = False #User first needs to confirm
        user_inst.save()

        context ={
                'user':user_inst,
                'http_protocol': getHTTP_Protocol(),
                'domain': get_current_site(self.request).domain,
                'token': account_activation_token.make_token(user_inst),
                'uid': urlsafe_base64_encode(force_bytes(user_inst.pk)).decode(),
                }

        mail_subject = 'Activate your gig account'
        mail_message_txt = render_to_string('users/messages/acc_activate_email.txt', context=context)

        user_inst.send_email(mail_subject, mail_message_txt)
        return redirect(self.get_success_url())


    def get_success_url(self):
        return reverse(self.success_url)


def reset_password_request_send(request):
    """
    A view that invites the user to confirm the 'the password reset request' through email confirmation.
    This view is called after a request was made to view `PasswordResetView`.
    """
    context= {
    'title_page': 'Password Reset',
    'title_msg': 'Confirmation Email Send',
    'short_message': 'A confirmation email was send. To confirm click on the link send to the email',
    'classes': '',
    }
    return render(request, 'users/short_message.html', context=context)


class PasswordResetConfirmView(auth_view.PasswordResetConfirmView):
    """
    View called once the user confirms the password reset. Through email confirmation.
    """
    template_name="users/password_reset_confirm.html"
    success_url='home'
    token_generator=account_activation_token


    def get_success_url(self):
        return reverse(self.success_url)


class PasswordResetView(auth_view.PasswordResetView):
    """
    View that provides the user with a PasswordResetForm.
    The form correctly filled will send an email to confirm the password reset.
    redirects to view `reset_password_request_send`.
    """
    template_name='users/password_reset_form.html'
    email_template_name="users/messages/password_reset_email.html"
    subject_template_name="users/messages/password_reset_subject.txt"
    success_url="users:password-reset-request-send"
    token_generator=account_activation_token


    def get_success_url(self):
        return reverse(self.success_url)

class LoginView(auth_view.LoginView):
    """
    View that provides the user with a LoginForm.
    """
    template_name="users/login.html"


class LogoutView(auth_view.LogoutView):
    """
    View for a Logout request made by the user.
    """
    template_name='gig/home.html'


class PasswordChangeView(auth_view.PasswordChangeView):
    """
    View that provides the user with a PasswordChange form.
    """

    template_name='users/password_change_form.html'
    success_url='home'

    def get_success_url(self):
        return reverse(self.success_url)


@login_required
def userProfileview(request):
    """
    View that returns the profile information associated with the user currently logged in.
    """
    if request.method =='GET':

        data = {
                'first_name': request.user.first_name,
                'last_name':request.user.last_name,
                'email': request.user.email,
                }
        form = UserProfileForm(initial=data)
        context= {'form': form,
                  'user': request.user,
                  'has_artistProfile': request.user.has_artistProfile(),
                  'has_bands': request.user.has_artistProfile() and request.user.artistmodel.has_bands(),
                  'has_ven': False}
        return render(request, "users/profile.html", context=context)
    else:

        if request.is_ajax():

            form =UserProfileForm(request.POST)
            if form.is_valid(request.user.email):
                if request.user.first_name == form.cleaned_data['first_name']:
                    msg_first=""
                else:
                    request.user.first_name = form.cleaned_data['first_name']
                    msg_first="changes saved"

                if request.user.last_name == form.cleaned_data['last_name']:
                    msg_last=""
                else:
                    request.user.last_name = form.cleaned_data['last_name']
                    msg_last="changes saved"

                request.user.save()
                data={
                    'is_valid': True,
                    'success_msgs': {'first_name': msg_first, "last_name": msg_last, "email": ""}
                }
                return JsonResponse(data)
            else:


                data= {'is_valid': False,
                       'error_msgs': form.errors_to_dict(),
                       }
                return JsonResponse(data)


def verify_email_existance(request):
    """
    View that responds only to ajax post requests. The view checks whether an account exists with similar 'email'.

    Expects key:
    `email`: which corresponds with the email on which the condition needs to be checked.

    Replies with JSON:
    {'is_taken': True} or {'is_taken': False}
    """
    if request.is_ajax():
        email=request.POST.get('email')
        return JsonResponse({'is_taken': User.objects.filter(email=email).exists()})
    else:
        return HttpResponseBadRequest()
