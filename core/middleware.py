from django.utils.timezone import now
from django.core.cache import cache

from users.utils import TokenManager


class TokenCacheMiddleware:
    """
    Middleware to handle caching and validation of authorization tokens.

    This middleware intercepts incoming HTTP requests to check for the presence of an
    "Authorization" token in the request headers. If the token is found, it validates the token
    against a cache and performs additional checks, such as expiration time, to ensure the token
    is still valid. If the token is invalid or expired, it removes the token from the cache.

    Attributes:
    get_response (Callable): The function that returns the response for a given HTTP request.
        It is typically the next middleware or view in the processing chain.

    Responsibilities:
    - Validate tokens from incoming HTTP requests.
    - Interact with a cache to check token statuses.
    - Remove tokens from the cache if they are close to expiration.

    Usage:
    Use this middleware in the Django middleware stack. It automatically processes HTTP
    requests to manage token validation and caching, without requiring manual interaction from views.

    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        token_key = request.headers.get("Authorization", "").split("Bearer ")[-1]
        if not token_key:
            return self.get_response(request)

        cached_token = cache.get(f"token_{token_key}")
        if cached_token:
            remaining_time = (cached_token.expires_at - now()).total_seconds()
            if remaining_time < 36000:  # Less than 10 hours
                TokenManager.remove_from_cache(token_key)

        return self.get_response(request)
