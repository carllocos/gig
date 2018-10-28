
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

from .forms import RegistrationForm, UserProfileForm
from .models import User
from .tokens import account_activation_token



#View for the users index
def index(request):
    return HttpResponse("users index")


#View for requesting a password to associate with users.models.User after signup with facebook or google
#TODO CREATE another form that only requests for password and confirm password
def request_password(request):
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
        context= {
        'title_page': 'Signup Confirmation',
        'title_msg': 'Confirmation Email Send',
        'short_message': 'To complete the registration click on the link send to the email',
        'classes': '',
        }
        return  render(request, 'users/short_message.html', context=context)

 #View to activate account after email confirmation
def activate_account(request, uidb64, token):
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


#TODO prevent header injection https://docs.djangoproject.com/en/2.1/topics/email/
#delete users in database after an amount of time that didn't manage to confirm the link

#View class that provides the SignupForm to the user
class SignupView(CreateView):
    form_class = RegistrationForm
    success_url = 'users:signup-confirm'
    model = User
    template_name = 'users/signup.html'

    def form_valid(self, form):

        user_inst = form.save(commit=False)
        user_inst.set_password(form.cleaned_data.get('password'))
        user_inst.is_active = False #User first needs to confirm
        user_inst.save()

        #auth.login(request=self.request, user=user_inst, backend='django.contrib.auth.backends.ModelBackend')
        context ={
                'user':user_inst,
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



def reset_password_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        user = User.get_user(email=email)
        if user:
            short_message = "We will soon reset password for {1}".format(email)
            return render(request, 'users/short_message.html', {'short_message': short_message})
        else:
            short_message = "No user register with {1}".format(email)
            return render(request, 'users/short_message.html', {'short_message': short_message})

    return HttpResponse("this is your form")


def reset_password_request_send(request):
    context= {
    'title_page': 'Password Reset',
    'title_msg': 'Confirmation Email Send',
    'short_message': 'A confirmation email was send. To confirm click on the link send to the email',
    'classes': '',
    }
    return render(request, 'users/short_message.html', context=context)


class PasswordResetConfirmView(auth_view.PasswordResetConfirmView):

    template_name="users/password_reset_confirm.html"
    success_url='home'
    token_generator=account_activation_token


    def get_success_url(self):
        return reverse(self.success_url)


class PasswordResetView(auth_view.PasswordResetView):
    template_name='users/password_reset_form.html'
    email_template_name="users/messages/password_reset_email.html"
    subject_template_name="users/messages/password_reset_subject.txt"
    success_url="users:password-reset-request-send"
    token_generator=account_activation_token


    def get_success_url(self):
        return reverse(self.success_url)

class LoginView(auth_view.LoginView):
    template_name="users/login.html"


class LogoutView(auth_view.LogoutView):
    template_name='gig/home.html'


class PasswordChangeView(auth_view.PasswordChangeView):
    template_name='users/password_change_form.html'
    success_url='home'

    def get_success_url(self):
        return reverse(self.success_url)


@login_required
def userProfileview(request):
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
    if request.is_ajax():
        email=request.POST.get('email')
        return JsonResponse({'is_taken': User.objects.filter(email=email).exists()})
    else:
        return HttpResponseBadRequest()
