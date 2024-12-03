from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed

from users.models import CustomAuthToken


class CustomJWTAuthentication(BaseAuthentication):
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
