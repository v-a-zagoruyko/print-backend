from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import LabelPreviewViewSet, ProductLabelViewSet, ContractorLabelViewSet

router = DefaultRouter()

router.register(r'label/preview', LabelPreviewViewSet, basename='label-preview')
router.register(r'label/product', ProductLabelViewSet, basename='product-label')
router.register(r'label/contractor', ContractorLabelViewSet, basename='contractor-label')

urlpatterns = [
    path('', include(router.urls)),
]
