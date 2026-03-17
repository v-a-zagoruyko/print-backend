import pytest

from main.models import (
    Template,
    ProductCategory,
    Product,
    ProductTemplate,
    ContractorCategory,
    Contractor,
    ContractorTemplate,
)


@pytest.fixture
def template(db):
    return Template.objects.create(name="T1", width=10, height=10, elements={})


@pytest.fixture
def product_with_template(db, template):
    cat = ProductCategory.objects.create(name="Food")
    p = Product.objects.create(
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
    ProductTemplate.objects.create(product=p, template=template)
    return p


@pytest.fixture
def contractor_with_template(db, template):
    cat = ContractorCategory.objects.create(name="CatA")
    c = Contractor.objects.create(category=cat, street="Street 1", name="Cont 1")
    ContractorTemplate.objects.create(contractor=c, template=template)
    return c


def test_template_layout_requires_auth(client):
    resp = client.post("/api/v1/labels/template/layout/", data={"width": "10.0", "height": "10.0", "elements": {}}, content_type="application/json")
    assert resp.status_code in {401, 403}


def test_template_layout_returns_image(client, contractor_user, monkeypatch):
    from main.services import label_service as label_service_module

    monkeypatch.setattr(label_service_module.label_service, "generate_template_png_preview_base64", lambda payload: "imgb64")
    client.force_login(contractor_user)
    resp = client.post(
        "/api/v1/labels/template/layout/",
        data={"width": "10.0", "height": "10.0", "elements": {}},
        content_type="application/json",
    )
    assert resp.status_code == 200
    assert resp.json() == {"image": "imgb64"}


def test_template_product_missing_template_returns_400(client, contractor_user, monkeypatch):
    from main.services import label_service as label_service_module

    monkeypatch.setattr(label_service_module.label_service, "generate_png_preview_base64", lambda template, payload: "imgb64")
    client.force_login(contractor_user)
    resp = client.post(
        "/api/v1/labels/template/product/",
        data={"name": "X"},
        content_type="application/json",
    )
    assert resp.status_code == 400
    assert resp.json() == {"error": "Missing field: template"}


def test_product_label_list_requires_print_operator(client, contractor_user):
    client.force_login(contractor_user)
    resp = client.get("/api/v1/labels/product/")
    assert resp.status_code in {403, 401}


def test_product_label_list_returns_products(client, print_operator_user, product_with_template):
    client.force_login(print_operator_user)
    resp = client.get("/api/v1/labels/product/")
    assert resp.status_code == 200
    data = resp.json()
    assert any(item["id"] == product_with_template.id for item in data)


def test_product_label_retrieve_returns_pdf(client, print_operator_user, product_with_template, monkeypatch):
    from main.services import label_service as label_service_module

    monkeypatch.setattr(label_service_module.label_service, "generate_pdf_preview_base64", lambda template, payload: "pdfb64")
    client.force_login(print_operator_user)
    resp = client.get(f"/api/v1/labels/product/{product_with_template.id}/")
    assert resp.status_code == 200
    assert resp.json()["pdf"] == "pdfb64"


def test_product_label_retrieve_passes_date_to_payload(client, print_operator_user, product_with_template, monkeypatch):
    from main.services import label_service as label_service_module

    captured = {}

    def _fake(template, payload):
        captured["payload"] = payload
        return "pdfb64"

    monkeypatch.setattr(label_service_module.label_service, "generate_pdf_preview_base64", _fake)

    client.force_login(print_operator_user)
    resp = client.get(f"/api/v1/labels/product/{product_with_template.id}/?date=2026-03-10")
    assert resp.status_code == 200
    payload = captured["payload"]
    assert payload["manufacture_date"] == "Изготовлено: 10.03.26 02:00"
    assert payload["expiry_date"] == "Употребить до: 10.03.26 02:00"


def test_contractor_label_list_returns_contractors(client, print_operator_user, contractor_with_template):
    client.force_login(print_operator_user)
    resp = client.get("/api/v1/labels/contractor/")
    assert resp.status_code == 200
    data = resp.json()
    assert any(item["id"] == contractor_with_template.id for item in data)


def test_contractor_label_retrieve_returns_pdf(client, print_operator_user, contractor_with_template, monkeypatch):
    from main.services import label_service as label_service_module

    monkeypatch.setattr(label_service_module.label_service, "generate_pdf_preview_base64", lambda template, payload: "pdfb64")
    client.force_login(print_operator_user)
    resp = client.get(f"/api/v1/labels/contractor/{contractor_with_template.id}/")
    assert resp.status_code == 200
    assert resp.json()["pdf"] == "pdfb64"

