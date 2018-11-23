
import string
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _




def lettersDigitsValidator(password):
    """
    Function that validates whether the password contans some characters.
    Raises an error if password doesn't contain a letter, digit or capital letter.
    """
    letters = set(string.ascii_letters)
    digits = set(string.digits)
    capitals = set(string.ascii_uppercase)
    psw = set(password)
    if psw.isdisjoint(letters) or psw.isdisjoint(digits) or psw.isdisjoint(capitals):
        raise ValidationError(
        _('Password must contain at least one digit, small- and capital letter'),
        params={},
        )

class LettersDigitsValidator:
    """
    similar as function `lettersDigitsValidator`
    """

    def validate(self, password, user=None):
        letters = set(string.ascii_letters)
        digits = set(string.digits)
        capitals = set(string.ascii_uppercase)
        psw = set(password)
        if psw.isdisjoint(letters) or psw.isdisjoint(digits) or psw.isdisjoint(capitals):
            raise ValidationError(
            _('Password must contain at least one digit, small- and capital letter'),
            params={},
            )


    def get_help_text(self):
        return _(
            "Your password must contain at least one digit, small- and capital letter"
            )



class MaxLengthValidator:
    """
    Validator that checks whether password contains at most `max_length` chars
    """

    def __init__(self, max_length):
        self.max_length=max_length

    def validate(self, password, user=None):
        if len(password) > self.max_length:
            raise ValidationError(
            _("This password must contain at most %(max_length)d characters."),
            code='password_too_long',
            params={'max_length': self.max_length},
            )

    def get_help_text(self):
        return _(
                "Your password must contain at most %(max_length)d characters."
                % {'max_length': self.max_length}
                )
