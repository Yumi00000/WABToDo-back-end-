from difflib import SequenceMatcher

from django.core.signing import Signer
from django.core.cache import cache
from django.utils.timezone import now

from users.models import CustomUser, CustomAuthToken
from users.tasks import send_email


def send_activation_email(request, user: CustomUser) -> None:
    """
    Sends an activation email to a user with a signed URL.

    This function generates a signed URL containing the user's ID and sends it via
    email. The signed URL is constructed using the Django Signer utility and the
    user's ID is securely embedded within the link. This link can be used to
    activate the user's account. The email is sent asynchronously using a celery
    task.

    Args:
        request: HttpRequest
            The HTTP request object, used to build the absolute activation URL.
        user: CustomUser
            The user object to whom the activation email will be sent. The email
            ID for the user is fetched from this object.

    Returns:
        None
    """
    user_signed = Signer().sign(user.id)
    signed_url = request.build_absolute_uri(f"/api/users/activate/{user_signed}")

    send_email.delay(user.email, signed_url)


class PasswordValidator:
    """
    Manages and validates password constraints for a given set of user attributes.

    This class is responsible for validating a password based on various rules and user data,
    including verifying the presence of capital letters and numbers, and ensuring the password
    does not contain personal information like the username, first name, last name, or email.
    It also checks for forbidden patterns such as spaces in the password. The class is designed
    to evaluate these constraints efficiently and return a boolean result indicating whether
    the password adheres to all specified rules.

    Attributes:
        _attrs: dict
            A dictionary of user attributes used for validation including password, username,
            first name, last name, and email.
        _password: str
            The password string being validated.

    """
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
    """
    Manages the creation, caching, and cleanup of authentication tokens for users.

    The TokenManager class provides functionalities to retrieve or create authentication
    tokens tied to a specific user and user agent, manage the caching of tokens to
    improve access efficiency, and clean up expired tokens from the database. It is
    designed to facilitate secure and efficient handling of authentication tokens in
    an application.

    Methods:
        - get_or_create_token: Retrieves or creates an authentication token for a
          user with respect to the user agent.
        - _cache_token: Caches the authentication token if it has a significant
          remaining lifetime.
        - remove_from_cache: Removes a specific token from the cache by its key.
        - cleanup_expired_tokens: Deletes all expired tokens from the database.
    """
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
