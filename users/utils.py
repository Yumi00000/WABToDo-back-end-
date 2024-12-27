from difflib import SequenceMatcher

from django.core.signing import Signer
from django.core.cache import cache
from django.utils.timezone import now

from users.models import CustomUser, CustomAuthToken
from users.tasks import send_email


def send_activation_email(request, user: CustomUser) -> None:
    """
    Sends an activation email to the user
    """
    user_signed = Signer().sign(user.id)
    signed_url = request.build_absolute_uri(f"/api/users/activate/{user_signed}")

    send_email.delay(user.email, signed_url)


class PasswordValidator:

    def __init__(self):
        self._attrs = {}
        self._password = ""

    def password_validator(self, attrs: dict) -> bool:
        """
        Returns True if the password is valid and False otherwise
        """

        self._attrs: dict = attrs
        self._password: str = attrs.get("password")

        return all(
            [
                self._password_has_capital_letter(),
                self._password_has_number(),
                not self._password_has_username(),
                not self._password_has_first_or_lastname(),
                not self._password_has_email(),
                not self._password_has_spaces(),
            ]
        )

    def _password_has_capital_letter(self):
        """
        Returns True if the password has at least one capital letter and False otherwise
        """
        return any(char.isupper() for char in self._password)

    def _password_has_number(self):
        """
        Returns True if the password has at least one number and False otherwise
        """
        return any(char.isdigit() for char in self._password)

    def _password_has_username(self) -> bool:
        """
        Returns True if the password has the username and False otherwise
        """
        lower_username = self._attrs.get("username").lower()
        lower_password = self._password.lower()

        if lower_username in lower_password or lower_username[::-1] in lower_password:
            return True

        similarity = SequenceMatcher(None, lower_username, lower_password).ratio()
        if similarity > 0.6:
            return True

        return False

    def _password_has_first_or_lastname(self) -> bool:
        """
        Returns True if the password has the first name or last name
        or if similarity more than 0.6
        and False otherwise
        """
        lower_first_name = self._attrs.get("first_name").lower()
        lower_last_name = self._attrs.get("last_name").lower()
        lower_password = self._password.lower()

        if lower_first_name in lower_password or lower_first_name[::-1] in lower_password:
            return True

        if lower_last_name in lower_password or lower_last_name[::-1] in lower_password:
            return True

        first_name_similarity = SequenceMatcher(None, lower_first_name, lower_password).ratio()
        last_name_similarity = SequenceMatcher(None, lower_last_name, lower_password).ratio()
        if first_name_similarity > 0.6 or last_name_similarity > 0.6:
            return True

        return False

    def _password_has_email(self) -> bool:
        """
        Returns True if the password has email or email name and False otherwise
        """
        lower_email = self._attrs.get("email").lower()
        lower_password = self._password.lower()
        email_name = lower_email.split("@")[0]

        if lower_email in lower_password or lower_email[::-1] in lower_password:
            return True

        if email_name in lower_password or email_name[::-1] in lower_password:
            return True

        return False

    def _password_has_spaces(self):
        """
        Returns True if the password has spaces or spaces and False otherwise
        """
        return True if " " in self._password else False


class TokenManager:

    def get_or_create_token(self, user, user_agent):
        token = CustomAuthToken.objects.filter(user=user, user_agent=user_agent).first()

        if token and token.is_valid():
            self._cache_token(token)
            return token, False

        if token:
            token.delete()

        new_token = CustomAuthToken.objects.create(user=user, user_agent=user_agent)
        self._cache_token(new_token)
        return new_token, True

    @staticmethod
    def _cache_token(token):
        """
        Add the token to the cache if the remaining lifetime is greater than 10 hours.
        """
        remaining_time = (token.expires_at - now()).total_seconds()
        if remaining_time > 36000:  # 10 hours
            cache.set(f"token_{token.key}", token, timeout=remaining_time)

    @staticmethod
    def remove_from_cache(token_key):
        """
        Removes token from the cache
        """
        cache.delete(f"token_{token_key}")

    @staticmethod
    def cleanup_expired_tokens():
        """
        Removes expired tokens from database
        """
        CustomAuthToken.objects.filter(expires_at__lte=now()).delete()
