from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ContractorOrderViewSet, ContractorUserListView, ProductListView

router = DefaultRouter()

router.register(r'contractor', ContractorOrderViewSet, basename='contractor-order')

urlpatterns = [
    path('products/', ProductListView.as_view(), name='orders-products'),
    path('contracts/', ContractorUserListView.as_view(), name='contractor-contracts'),
    path('', include(router.urls)),
]
