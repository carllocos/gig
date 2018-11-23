from django.urls import path, re_path

from . import views


app_name = 'users'



urlpatterns = [
    path('', views.index, name="register-index"),
    path('profile/', views.userProfileview, name='profile'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    path('signup/', views.SignupView.as_view(), name='signup'),
    path('signup/ajax/', views.verify_email_existance, name='signup-ajax'),
    path('update_email/', views.update_email, name='update-email'),
    re_path(r'^update_email/confirm/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/(?P<eid64>[0-9A-Za-z_\-]+)$', views.update_email_confirm, name='update-email-confirm'),

    path('signup/request_password/', views.request_password, name='request-password'),

    #URL register/confirm corresponds with the html that tells you to confirm your registration
    path('signup/confirm/', views.confirm_account, name='signup-confirm'),
    #URL register/confirm/uid/token is the link that the user clicks to confirm registration
    re_path(r'^signup/confirm/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$', views.activate_account, name='signup-confirm-complete'),
    path('changepassword/', views.PasswordChangeView.as_view(), name='password-change'),
    #path('resetpassword/', views.reset_password_view, name='password-reset'),

    path('resetpassword/', views.PasswordResetView.as_view(), name='password-reset'),

    re_path(r'^resetpassword/confirm/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$',
                            views.PasswordResetConfirmView.as_view(),name='password-reset-confirmed'),
    path('resetpassword/requestsend/',views.reset_password_request_send, name= 'password-reset-request-send')

]
