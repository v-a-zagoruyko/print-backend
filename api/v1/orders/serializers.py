#TODO: добавить logging
from django.db import transaction
from django.utils import timezone
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from main.models import Product
from orders.models import ContractorUser, ContractorOrderItem, ContractorOrder


class OrderDateQuerySerializer(serializers.Serializer):
    date = serializers.DateField(required=False)

    def get_date(self):
        return self.validated_data.get("date") or timezone.localdate()


class ProductCartSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ("id", "name", "weight", "barcode", "quantity")


class ProductDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ("id", "name", "barcode",)


class ContractorUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContractorUser
        fields = ("id",)


class ContractorOrderItemSerializer(serializers.ModelSerializer):
    product = ProductDetailSerializer()

    class Meta:
        model = ContractorOrderItem
        fields = ("product", "quantity",)


class ContractorOrderItemCreateSerializer(serializers.ModelSerializer):
    product = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all())

    class Meta:
        model = ContractorOrderItem
        fields = ("product", "quantity",)


class ContractorOrderListSerializer(serializers.ModelSerializer):
    contractor_id = serializers.IntegerField(source='contractor_user.id')
    order_id = serializers.IntegerField(source='id')

    class Meta:
        model = ContractorOrder
        fields = ("contractor_id", "order_id", "date", "status",)


class ContractorOrderDetailSerializer(serializers.ModelSerializer):
    order_id = serializers.IntegerField(source='id')
    contractor_id = serializers.IntegerField(source='contractor_user.id')
    date = serializers.DateField(required=False)
    items = ContractorOrderItemSerializer(source="order_items", many=True, read_only=True)

    class Meta:
        model = ContractorOrder
        fields = ("contractor_id", "order_id", "status", "date", "items",)


class ContractorOrderCreateOrUpdateSerializer(serializers.ModelSerializer):
    contractor_user_id = serializers.IntegerField()
    date = serializers.DateField(required=False)
    items = ContractorOrderItemCreateSerializer(many=True, write_only=True)

    class Meta:
        model = ContractorOrder
        fields = ("contractor_user_id", "date", "items",)

    def create(self, validated_data):
        request = self.context.get("request")
        items_data = validated_data.pop("items")
        contractor_user_id = validated_data.pop("contractor_user_id")
        date = validated_data.pop("date", None)

        if date is None:
            date = self.context.get("date") or timezone.localdate()

        try:
            contractor_user = ContractorUser.objects.get(pk=contractor_user_id, user=request.user)
        except ContractorUser.DoesNotExist:
            raise ValidationError("Контрагент не найден или не принадлежит пользователю")

        if ContractorOrder.objects.filter(
            contractor_user=contractor_user,
            date=date,
            status__in=[ContractorOrder.Status.CREATED, ContractorOrder.Status.PROCESSED]
        ).exists():
            raise ValidationError("Заказ уже существует или отгружен")

        with transaction.atomic():
            order = ContractorOrder.objects.create(contractor_user=contractor_user, date=date)
            items_to_create = []
            for item in items_data:
                items_to_create.append(ContractorOrderItem(order=order, **item))
            ContractorOrderItem.objects.bulk_create(items_to_create)
        return order

    def update(self, instance, validated_data):
        items_data = validated_data.pop("items", [])
        existing_items_qs = instance.order_items.select_related("product").all()
        items_to_update = []
        items_to_create = []
        pids_to_delete = []

        for item in items_data:
            product = item.get("product")
            quantity = item.get("quantity", 0)
            if existing_items_qs.filter(product=product).exists():
                if quantity == 0:
                    pids_to_delete.append(product.pk)
                else:
                    obj = existing_items_qs.get(product=product)
                    obj.quantity = quantity
                    items_to_update.append(obj)
            else:
                if quantity > 0:
                    items_to_create.append(ContractorOrderItem(order=instance, **item))

        with transaction.atomic():
            if pids_to_delete:
                instance.order_items.filter(product_id__in=pids_to_delete).delete()
            if items_to_update:
                ContractorOrderItem.objects.bulk_update(items_to_update, ["quantity"])
            if items_to_create:
                ContractorOrderItem.objects.bulk_create(items_to_create)
        instance.updated_at = timezone.now()
        instance.save()
        return instance
