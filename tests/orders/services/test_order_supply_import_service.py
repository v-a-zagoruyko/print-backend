import io

import pandas as pd
import pytest
from django.utils import timezone

from main.models import ContractorCategory, Contractor, ProductCategory, Product
from orders.models import ContractorUser, ContractorOrder, ContractorOrderItem, OrderSupply
from orders.services.order_supply_import_service import (
    OrderSupplyImportError,
    OrderSupplyImportService,
)


@pytest.fixture
def product(db):
    category = ProductCategory.objects.create(name="Food")
    return Product.objects.create(
        category=category,
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


def _make_excel_bytes(rows):
    df = pd.DataFrame(rows)
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False)
    buffer.seek(0)
    return buffer.getvalue()


def test_order_supply_import_service_creates_entities(db, django_user_model, product):
    user = django_user_model.objects.create(username="admin")

    today = timezone.localdate()
    rows = [
        {
            "Дата заказа": today,
            "Название склада": "Склад 1",
            "Штрихкод": product.barcode,
            "Количество": 3,
        }
    ]
    excel_bytes = _make_excel_bytes(rows)
    uploaded_file = io.BytesIO(excel_bytes)

    service = OrderSupplyImportService(uploaded_file, user)
    result = service.import_data()

    assert isinstance(result.order_supply, OrderSupply)
    assert result.order_supply.date == today

    contractor_user = ContractorUser.objects.get(user=user)
    contractor_order = ContractorOrder.objects.get(contractor_user=contractor_user, date=today)
    item = ContractorOrderItem.objects.get(order=contractor_order, product=product)

    assert item.quantity == 3
    assert contractor_order in result.order_supply.orders.all()
    assert not result.missing_barcodes


def test_order_supply_import_service_missing_product_is_reported(db, django_user_model):
    user = django_user_model.objects.create(username="admin")
    today = timezone.localdate()
    rows = [
        {
            "Дата заказа": today,
            "Название склада": "Склад 1",
            "Штрихкод": "0000000000000",
            "Количество": 1,
        }
    ]
    excel_bytes = _make_excel_bytes(rows)
    uploaded_file = io.BytesIO(excel_bytes)

    service = OrderSupplyImportService(uploaded_file, user)
    result = service.import_data()

    assert result.missing_barcodes == ["0000000000000"]
    assert ContractorOrderItem.objects.count() == 0


def test_order_supply_import_service_raises_on_multiple_dates(db, django_user_model):
    user = django_user_model.objects.create(username="admin")
    today = timezone.localdate()
    tomorrow = today + timezone.timedelta(days=1)

    rows = [
        {
            "Дата заказа": today,
            "Название склада": "Склад 1",
            "Штрихкод": "0000000000000",
            "Количество": 1,
        },
        {
            "Дата заказа": tomorrow,
            "Название склада": "Склад 1",
            "Штрихкод": "0000000000000",
            "Количество": 1,
        },
    ]
    excel_bytes = _make_excel_bytes(rows)
    uploaded_file = io.BytesIO(excel_bytes)

    service = OrderSupplyImportService(uploaded_file, user)
    with pytest.raises(OrderSupplyImportError):
        service.import_data()

