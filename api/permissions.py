from rest_framework.permissions import BasePermission


class IsPrintOperator(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user.is_superuser
            or request.user.groups.filter(name='Печатник').exists()
        )


class IsContractor(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user.is_superuser
            or request.user.groups.filter(name='Контрагент').exists()
        )
