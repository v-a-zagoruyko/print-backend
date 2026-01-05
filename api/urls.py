from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import InfoView, TemplateLabelViewSet, ProductLabelViewSet, ContractorLabelViewSet, qz_cert, qz_sign

router = DefaultRouter()

router.register(r'label/preview', TemplateLabelViewSet, basename='template-label')
router.register(r'label/product', ProductLabelViewSet, basename='product-label')
router.register(r'label/contractor', ContractorLabelViewSet, basename='contractor-label')

urlpatterns = [
    path('', include(router.urls)),
    path("qz/cert/", qz_cert, name="qz_cert"),
    path("qz/sign/", qz_sign, name="qz_sign"),
    path("user/", InfoView.as_view(), name="user"),
]
