from rest_framework.viewsets import ViewSet
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from main.models import Product
from orders.models import ContractorUser, ContractorOrder
from api.common.permissions import IsContractor
from .serializers import (
    ContractorUserSerializer,
    ProductDetailSerializer,
    ContractorOrderListSerializer,
    ContractorOrderDetailSerializer,
    ContractorOrderCreateOrUpdateSerializer,
    OrderDateQuerySerializer,
)


class ContractorUserListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        users = ContractorUser.objects.filter(
            user=request.user,
            status=ContractorUser.Status.ACTIVE,
        )
        serializer = ContractorUserSerializer(users, many=True)
        return Response(serializer.data)


class ProductListView(APIView):
    permission_classes = [IsAuthenticated, IsContractor]

    def get(self, request):
        products = Product.objects.filter(
            status=Product.ProductStatus.AVAILABLE,
        ).order_by("name")
        serializer = ProductDetailSerializer(products, many=True)
        return Response(serializer.data)


class ContractorOrderViewSet(ViewSet):
    permission_classes = [IsAuthenticated, IsContractor]

    def _get_date(self, request):
        serializer = OrderDateQuerySerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        return serializer.get_date()

    def list(self, request):
        user_contractors = ContractorUser.objects.filter(user=request.user)
        orders = ContractorOrder.objects.filter(contractor_user__in=user_contractors)
        serializer = ContractorOrderListSerializer(orders, many=True)
        return Response(serializer.data)

    def retrieve(self, request, pk=None):
        contractor_user = get_object_or_404(ContractorUser, pk=pk, user=request.user)
        date = self._get_date(request)
        order = get_object_or_404(ContractorOrder, contractor_user=contractor_user, date=date)
        serializer = ContractorOrderDetailSerializer(order)
        return Response(serializer.data)

    def partial_update(self, request, pk=None):
        contractor_user = get_object_or_404(ContractorUser, pk=pk, user=request.user)
        date = self._get_date(request)
        order = get_object_or_404(ContractorOrder, contractor_user=contractor_user, date=date)
        serializer = ContractorOrderCreateOrUpdateSerializer(order, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(ContractorOrderDetailSerializer(order).data, status=200)

    def create(self, request):
        date = self._get_date(request)
        serializer = ContractorOrderCreateOrUpdateSerializer(
            data=request.data,
            context={"request": request, "date": date},
        )
        serializer.is_valid(raise_exception=True)
        order = serializer.save()
        return Response(ContractorOrderDetailSerializer(order).data, status=201)
