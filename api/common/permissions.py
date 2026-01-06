from enum import StrEnum
from rest_framework.permissions import BasePermission


class UserGroup(StrEnum):
    PRINT_OPERATOR = "Печатник"
    CONTRACTOR = "Контрагент"


def user_in_group(user, group: UserGroup) -> bool:
    if not user or not user.is_authenticated:
        return False
    return group.value in user.groups.values_list("name", flat=True)


class IsInGroup(BasePermission):
    group: UserGroup | None = None

    def has_permission(self, request, view):
        if not self.group:
            return False
        return (
            request.user.is_superuser
            or user_in_group(request.user, self.group)
        )


class IsPrintOperator(IsInGroup):
    group = UserGroup.PRINT_OPERATOR


class IsContractor(IsInGroup):
    group = UserGroup.CONTRACTOR
