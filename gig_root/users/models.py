from django.contrib.auth.models import BaseUserManager

class UserManger(BaseUserManager):

    def _create_user(self, email, first_name, last_name, password, is_active, is_staff, is_superuser, **kwargs):
        user = self.model(
                    email=self.normalize_email(email),
                    first_name=first_name,
                    last_name=last_name,
                    is_active=is_active,
                    is_staff=is_staff,
                    **kwargs)


        user.set_password(password)
        user.is_superuser =is_superuser
        user.save(using=self._db)
        return user

    def create_user(self, email, first_name, last_name, password, **kwargs):
        return self._create_user(email, first_name, last_name, password, True, False, False, **kwargs)

    def create_superuser(self, email, password, first_name="", last_name="", **kwargs):
        if first_name == '':
            first_name= email
        return self._create_user(email, first_name, last_name, password, True, True, True,**kwargs)


from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.core.mail import EmailMessage
from django.core.exceptions import ObjectDoesNotExist

class User(AbstractBaseUser, PermissionsMixin):

    USERNAME_FIELD ="email"

    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    password = models.CharField(max_length=320)
    is_active = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    objects = UserManger()


    def __str__(self):
        return self.get_full_name()


    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"

    def get_short_name(self):
        return f"{self.first_name}"


    def send_email(self, mail_subject, mail_message_txt):
        """
        `send_email` method sends an email to the corresping user with `mail_subject` as subject and `mail_message_txt` as content of the email.
        The email account used to send the email is the default account associated with the gig web app. 
        """
        email = EmailMessage(subject=mail_subject, body=mail_message_txt, to=[self.email])
        email.send(fail_silently=True)


    @staticmethod
    def get_user(email, default=False):
        """
        `get_user` is a static method that retrieves an user based on the given `email`.
        If the user don't exists `default` is returned.
        """
        try:
            return User.objects.get(email=email)
        except:
            return default



    def get_artist(self, default=False):
        """
        return an ArtistProfile instance associated to the user or `default` if
        the profile don't exists.
        """
        if self.has_artistProfile():
            return self.artistmodel
        else:
            return default

    def has_artistProfile(self):
        """
        Test wheter the user has an ArtistProfile associated to it.
        """
        try:
            self.artistmodel
            return True
        except ObjectDoesNotExist:
            return False
