import jwt
from asgiref.sync import sync_to_async
from django.conf import settings
from django.contrib.auth.models import AnonymousUser

from users.models import CustomUser

@sync_to_async
def get_user_from_id(user_id):
    try:
        return CustomUser.objects.get(id=user_id)
    except CustomUser.DoesNotExist:
        return AnonymousUser()

class WebSocketJWTAuthMiddleware:
    """
    Custom middleware to authenticate WebSocket connections using JWT.
    """

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        # Extract the token from the query string
        query_string = scope.get("query_string", b"").decode("utf-8")
        query_params = dict(param.split("=") for param in query_string.split("&") if "=" in param)
        token = query_params.get("token", None)

        if token:
            try:
                # Decode the JWT token
                payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
                user_id = payload.get("user_id")

                # Fetch the user
                scope["user"] = await get_user_from_id(user_id)
            except jwt.ExpiredSignatureError:
                scope["user"] = AnonymousUser()  # Token expired
            except jwt.InvalidTokenError:
                scope["user"] = AnonymousUser()  # Invalid token
        else:
            scope["user"] = AnonymousUser()  # No token provided

        # Pass the scope to the app
        return await self.app(scope, receive, send)
