from datetime import timedelta

from django.conf import settings
from django.http import HttpRequest, HttpResponse
from django.contrib.auth import get_user

from ipware import get_client_ip
from redis import Redis


redis_default = Redis.from_url(url=settings.CACHES["default"]["LOCATION"])
PERIOD = timedelta(seconds=1)
AUTHENTICATED_LIMIT = 20
ANONYMOUS_LIMIT = 10


def get_request_identifier(request: HttpRequest) -> tuple[str, int]:
    """
    Determines the identifier and rate limit for the request based on authentication status.
    Returns a tuple of (identifier, limit).
    """
    user = get_user(request)

    if user and user.is_authenticated:
        # Use username for authenticated users
        return f"user:{user.username}", AUTHENTICATED_LIMIT

    # Fall back to IP address for anonymous users
    ip, is_routable = get_client_ip(request)
    if not ip:
        ip = "unknown"
    return f"ip:{ip}", ANONYMOUS_LIMIT


def request_is_limited(
    red: Redis, redis_key: str, redis_limit: int, redis_period: timedelta
) -> bool:
    """
    Check if the request should be rate limited.
    Returns True if request should be limited, False otherwise.
    """
    if red.setnx(redis_key, redis_limit):
        red.expire(redis_key, int(redis_period.total_seconds()))
    bucket_val = red.get(redis_key)
    if bucket_val and int(bucket_val) > 0:
        red.decrby(redis_key, 1)
        return False
    return True


def rate_limiter(get_response):
    """
    Django middleware for rate limiting requests based on authentication status.
    Uses username for authenticated users and IP address for anonymous users.
    """

    def middleware(request: HttpRequest) -> HttpResponse:
        if request.method == "POST":
            identifier, limit = get_request_identifier(request)
            rate_limit_key = f"{identifier}:{request.path}:post"
            if request_is_limited(redis_default, rate_limit_key, limit, PERIOD):
                return HttpResponse(
                    "Too many requests, please try again later.", status=429
                )
        response = get_response(request)
        return response

    return middleware
