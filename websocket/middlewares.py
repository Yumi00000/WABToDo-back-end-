import jwt
from asgiref.sync import sync_to_async
from django.conf import settings
from django.contrib.auth.models import AnonymousUser

from users.models import CustomUser


@sync_to_async
def get_user_from_id(user_id):
    """
    Fetch a user by their ID asynchronously, or return an AnonymousUser if no user with the
    specified ID exists.

    @param user_id: The unique identifier of the user to fetch.
    @type user_id: int

    @return: The user object with the specified ID if found, otherwise an AnonymousUser.
    """
    try:
        return CustomUser.objects.get(id=user_id)
    except CustomUser.DoesNotExist:
        return AnonymousUser()


class WebSocketJWTAuthMiddleware:
    """
    Middleware for authenticating WebSocket connections using JWT.

    This middleware is designed to authenticate WebSocket connections
    by extracting a JWT token from the query string of the connection
    and validating it. The decoded payload of the JWT token is used to
    set the authenticated user in the connection scope. If the token
    is missing, expired, or invalid, the user is set as an anonymous
    user. This middleware is specifically intended for integration
    within WebSocket-based applications.

    Attributes:
        app (Any): A callable representing the application or ASGI app
        that this middleware wraps. It acts as the next layer in the
        middleware stack or the final application.

    Methods:
        __call__: Asynchronous callable method that processes the
        WebSocket connection, validates the JWT token, assigns the
        corresponding user to the connection scope, and forwards the
        connection to the next layer or application.
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
