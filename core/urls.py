from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include
from django.contrib import admin
from .views import health, qz_cert, qz_sign, post_login_redirect

urlpatterns = [
    path("api/", include("api.urls")),
    path("health/", health, name="health"),
    path("qz/cert/", qz_cert, name="qz_cert"),
    path("qz/sign/", qz_sign, name="qz_sign"),
    path("post_login_redirect/", post_login_redirect, name="post-login-redirect"),
    path("", admin.site.urls),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
