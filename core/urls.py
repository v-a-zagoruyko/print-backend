from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include
from django.contrib import admin
from .views import health, post_login_redirect

urlpatterns = [
    path("api/", include("api.urls")),
    path("health/", health, name="health"),
    path("post_login_redirect/", post_login_redirect, name="post-login-redirect"),
    path("", admin.site.urls),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
