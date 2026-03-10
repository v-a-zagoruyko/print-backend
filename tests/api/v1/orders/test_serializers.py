import pytest
from django.utils import timezone
from rest_framework.exceptions import ValidationError
from rest_framework.test import APIRequestFactory

from api.v1.orders.serializers import ContractorOrderCreateOrUpdateSerializer
from main.models import ContractorCategory, Contractor, ProductCategory, Product
from orders.models import ContractorUser, ContractorOrder, ContractorOrderItem, OrderSupply


@pytest.fixture
def product(db):
    cat = ProductCategory.objects.create(name="Food")
    return Product.objects.create(
        category=cat,
        name="Product 1",
        ingredients="Ing",
        weight="100g",
        best_before=3,
        calories="10.00",
        protein="1.00",
        fat="1.00",
        carbs="1.00",
        barcode="1234567890123",
    )


@pytest.fixture
def contractor_user_obj(db, contractor_user):
    category = ContractorCategory.objects.create(name="CatA")
    contractor = Contractor.objects.create(category=category, street="Street 1")
    return ContractorUser.objects.create(contractor=contractor, user=contractor_user)


def _request_for(user):
    factory = APIRequestFactory()
    req = factory.post("/api/v1/orders/contractor/")
    req.user = user
    return req


def test_order_serializer_creates_order_and_items(db, contractor_user, contractor_user_obj, product):
    date = timezone.localdate()
    data = {
        "contractor_user_id": contractor_user_obj.id,
        "date": date.isoformat(),
        "items": [{"product": product.id, "quantity": 2}],
    }
    serializer = ContractorOrderCreateOrUpdateSerializer(
        data=data,
        context={"request": _request_for(contractor_user), "date": date},
    )
    assert serializer.is_valid(), serializer.errors
    order = serializer.save()

    assert ContractorOrder.objects.filter(pk=order.pk).exists()
    items = list(ContractorOrderItem.objects.filter(order=order))
    assert len(items) == 1
    assert items[0].product_id == product.id
    assert items[0].quantity == 2


def test_order_serializer_rejects_other_users_contractor(db, contractor_user, other_contractor_user, product):
    category = ContractorCategory.objects.create(name="CatB")
    contractor = Contractor.objects.create(category=category, street="Street 2")
    cu_other = ContractorUser.objects.create(contractor=contractor, user=other_contractor_user)

    date = timezone.localdate()
    data = {
        "contractor_user_id": cu_other.id,
        "date": date.isoformat(),
        "items": [{"product": product.id, "quantity": 1}],
    }
    serializer = ContractorOrderCreateOrUpdateSerializer(
        data=data,
        context={"request": _request_for(contractor_user), "date": date},
    )
    assert serializer.is_valid(), serializer.errors
    with pytest.raises(ValidationError):
        serializer.save()


def test_order_serializer_rejects_duplicate_order(db, contractor_user, contractor_user_obj, product):
    date = timezone.localdate()
    ContractorOrder.objects.create(contractor_user=contractor_user_obj, date=date, status=ContractorOrder.Status.CREATED)

    data = {
        "contractor_user_id": contractor_user_obj.id,
        "date": date.isoformat(),
        "items": [{"product": product.id, "quantity": 1}],
    }
    serializer = ContractorOrderCreateOrUpdateSerializer(
        data=data,
        context={"request": _request_for(contractor_user), "date": date},
    )
    assert serializer.is_valid(), serializer.errors
    with pytest.raises(ValidationError):
        serializer.save()


def test_order_serializer_update_deletes_item_when_quantity_zero(db, contractor_user, contractor_user_obj, product):
    date = timezone.localdate()
    order = ContractorOrder.objects.create(contractor_user=contractor_user_obj, date=date, status=ContractorOrder.Status.CREATED)
    ContractorOrderItem.objects.create(order=order, product=product, quantity=5)

    serializer = ContractorOrderCreateOrUpdateSerializer(
        instance=order,
        data={"items": [{"product": product.id, "quantity": 0}]},
        partial=True,
        context={"request": _request_for(contractor_user), "date": date},
    )
    assert serializer.is_valid(), serializer.errors
    serializer.save()

    assert ContractorOrderItem.objects.filter(order=order, product=product).count() == 0

