import pytest
from django.utils import timezone
from django.contrib.auth.models import Group

from main.models import ContractorCategory, Contractor
from orders.models import ContractorUser, ContractorOrder


@pytest.fixture
def contractor_a(db, contractor_user):
    category = ContractorCategory.objects.create(name="CatA")
    contractor = Contractor.objects.create(category=category, street="Street 1")
    return ContractorUser.objects.create(contractor=contractor, user=contractor_user)


@pytest.fixture
def contractor_b(db, other_contractor_user):
    category = ContractorCategory.objects.create(name="CatB")
    contractor = Contractor.objects.create(category=category, street="Street 2")
    return ContractorUser.objects.create(contractor=contractor, user=other_contractor_user)


def test_contractor_list_only_shows_own_orders(client, contractor_user, contractor_group, contractor_a, contractor_b):
    # Ensure group exists and is assigned (fixture already does it).
    today = timezone.localdate()
    ContractorOrder.objects.create(contractor_user=contractor_a, date=today)
    ContractorOrder.objects.create(contractor_user=contractor_b, date=today)

    client.force_login(contractor_user)
    resp = client.get("/api/v1/orders/contractor/")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["contractor_id"] == contractor_a.id


def test_contractor_cannot_retrieve_other_contractors_order(client, contractor_user, contractor_a, contractor_b):
    today = timezone.localdate()
    ContractorOrder.objects.create(contractor_user=contractor_b, date=today)

    client.force_login(contractor_user)
    resp = client.get(f"/api/v1/orders/contractor/{contractor_b.id}/?date={today.isoformat()}")
    assert resp.status_code in {403, 404}

