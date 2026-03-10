from django.urls import path, include

urlpatterns = [
    path("labels/", include("api.v1.labels.urls")),
    path("orders/", include("api.v1.orders.urls")),
    path("system/", include("api.v1.system.urls")),
]
