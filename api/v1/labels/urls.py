from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TemplateLabelViewSet, ProductLabelViewSet, ContractorLabelViewSet

router = DefaultRouter()

router.register(r'template', TemplateLabelViewSet, basename='template-label')
router.register(r'product', ProductLabelViewSet, basename='product-label')
router.register(r'contractor', ContractorLabelViewSet, basename='contractor-label')

urlpatterns = [
    path('', include(router.urls)),
]
