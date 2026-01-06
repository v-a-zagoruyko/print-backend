from django.urls import path, include

urlpatterns = [
    path("labels/", include("api.v1.labels.urls")),
    path("system/", include("api.v1.system.urls")),
]
