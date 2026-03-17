import io
import zipfile

import pytest
from django.utils import timezone

from main.models import ContractorCategory, Contractor, ProductCategory, Product
from orders.models import ContractorUser, ContractorOrder, ContractorOrderItem, OrderSupply
from orders.services.order_excel_service import OrderExcelService


@pytest.fixture
def product(db):
    cat = ProductCategory.objects.create(name="Food")
    return Product.objects.create(
        category=cat,
        name="Product 1",
        price=100,
        ingredients="Ing",
        weight="100g",
        calories="10.00",
        protein="1.00",
        fat="1.00",
        carbs="1.00",
        barcode="1234567890123",
    )


def test_order_excel_service_generates_valid_xlsx_bytes(db, contractor_user, product):
    category = ContractorCategory.objects.create(name="CatA")
    contractor = Contractor.objects.create(category=category, street="Street 1")
    cu = ContractorUser.objects.create(contractor=contractor, user=contractor_user)

    today = timezone.localdate()
    order = ContractorOrder.objects.create(contractor_user=cu, date=today, status=ContractorOrder.Status.CREATED)
    ContractorOrderItem.objects.create(order=order, product=product, quantity=2)

    supply = OrderSupply.objects.create(date=today)
    supply.orders.add(order)

    xlsx_bytes, filename = OrderExcelService(supply).generate_xlsx_bytes()

    assert filename.endswith(".xlsx")
    assert str(today.strftime("%d.%m.%Y")) in filename
    assert isinstance(xlsx_bytes, (bytes, bytearray))
    assert xlsx_bytes[:2] == b"PK"  # xlsx is a zip archive

    with zipfile.ZipFile(io.BytesIO(xlsx_bytes)) as zf:
        names = set(zf.namelist())
        assert "[Content_Types].xml" in names
        assert "xl/workbook.xml" in names

