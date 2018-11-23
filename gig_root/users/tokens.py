from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils import six


class TokenGenerator(PasswordResetTokenGenerator):
    """
    Customized TokenGenerator. Generates tokens based on the primary key `timestamp` and `is_active` state
    of the `user`.
    """

    def _make_hash_value(self, user, timestamp):
        return ( six.text_type(user.pk) + six.text_type(timestamp) + six.text_type(user.is_active))



account_activation_token = TokenGenerator()
