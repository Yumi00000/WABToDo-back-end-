from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed

from users.models import CustomAuthToken


class CustomJWTAuthentication(BaseAuthentication):
    """
    Custom authentication class for validating JWT tokens in HTTP requests.

    This class is intended to authenticate users by verifying JWT-based tokens
    passed in the 'Authorization' header of HTTP requests. It ensures that only
    tokens of type 'Bearer' are accepted and checks their validity against
    stored authentication tokens. If validation is successful, it returns the
    associated user and token, enabling further processing of the request in an
    authenticated context.
    """
    def authenticate(self, request):
        auth_header = request.META.get("HTTP_AUTHORIZATION")
        if not auth_header:
            return None

        try:
            token_type, token = auth_header.split()
            if token_type != "Bearer":
                raise AuthenticationFailed("Invalid Token type")

            token = CustomAuthToken.objects.get(key=token)

        except (ValueError, CustomAuthToken.DoesNotExist):
            raise AuthenticationFailed("Invalid Token")

        return token.user, token
