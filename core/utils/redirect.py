from urllib.parse import urlparse
from django.conf import settings


def get_origin(url):
    parsed = urlparse(url)
    if not parsed.scheme or not parsed.netloc:
        return None
    return f"{parsed.scheme}://{parsed.netloc}"

def is_allowed_redirect_url(url):
    origin = get_origin(url)
    if not origin:
        return False
    return origin in settings.CORS_ALLOWED_ORIGINS
