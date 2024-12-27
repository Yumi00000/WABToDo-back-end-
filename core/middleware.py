from django.utils.timezone import now
from django.core.cache import cache

from users.utils import TokenManager


class TokenCacheMiddleware:
    """
    Middleware for managing tokens in the cache.
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
            if remaining_time < 36000:  # Less than 10 часов
                TokenManager.remove_from_cache(token_key)
