from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ContractorOrderViewSet

router = DefaultRouter()

router.register(r'contractor', ContractorOrderViewSet, basename='contractor-order')

urlpatterns = [
    path('', include(router.urls)),
]
