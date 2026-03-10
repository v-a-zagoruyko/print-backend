import pytest
from django.contrib.auth.models import Group, User


@pytest.fixture
def contractor_group(db):
    return Group.objects.get_or_create(name="Контрагент")[0]


@pytest.fixture
def print_operator_group(db):
    return Group.objects.get_or_create(name="Печатник")[0]


@pytest.fixture
def contractor_user(db, contractor_group):
    user = User.objects.create_user(username="contractor", password="pass")
    user.groups.add(contractor_group)
    return user


@pytest.fixture
def other_contractor_user(db, contractor_group):
    user = User.objects.create_user(username="other_contractor", password="pass")
    user.groups.add(contractor_group)
    return user


@pytest.fixture
def print_operator_user(db, print_operator_group):
    user = User.objects.create_user(username="print_operator", password="pass")
    user.groups.add(print_operator_group)
    return user

