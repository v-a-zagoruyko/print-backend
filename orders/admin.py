import logging
from urllib.parse import quote
from django.contrib import admin
from django.http import HttpResponse
from django.shortcuts import redirect
from simple_history.admin import SimpleHistoryAdmin
from .services.order_excel_service import OrderExcelService
from .models import ContractorUser, ContractorOrder, ContractorOrderItem, OrderSupply
from .forms import OrderSupplyForm

logger = logging.getLogger(__name__)


@admin.register(ContractorUser)
class ContractorUserAdmin(admin.ModelAdmin):
    list_display = ["user", "user__first_name", "user__last_name", "user__email", "contractor__name", "contractor__street", "status"]
    search_fields = ["user__username", "user__last_name", "user__email", "contractor__name", "contractor__street",]
    autocomplete_fields = ["user", "contractor",]
    list_filter = ["status", "contractor__category", "contractor__city",]

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return ["user", "contractor",]
        return []

    def has_delete_permission(self, request, obj=None):
        return False


class ContractorOrderItemInline(admin.TabularInline):
    model = ContractorOrderItem
    fields = ["product", "quantity",]
    autocomplete_fields = ["product",]
    extra = 1


@admin.register(ContractorOrder)
class ContractorOrderAdmin(SimpleHistoryAdmin):
    list_display = ["contractor_user", "contractor_user__user", "status", "date",]
    list_filter = ["date", "status",]
    autocomplete_fields = ["contractor_user",]
    search_fields = ["contractor_user__user",]
    inlines = [ContractorOrderItemInline,]

    def change_view(self, request, object_id, form_url='', extra_context=None):
        obj = self.get_object(request, object_id)
        if not obj:
            return
        if '_cancel' in request.POST:
            content, filename = OrderExcelService(obj).generate_xlsx_bytes()
            response = HttpResponse(
                content,
                content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
            response['Content-Disposition'] = f"attachment; filename*=UTF-8''{quote(filename)}"
            return response
        return super().change_view(request, object_id, form_url, extra_context)

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return ["status", "date", "contractor_user", "created_at", "updated_at",]
        return ["status",]

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(OrderSupply)
class OrderSupplyAdmin(SimpleHistoryAdmin):
    change_form_template = "admin/order_excel_download.html"
    form = OrderSupplyForm

    list_display = ["created_at", "date", "updated_at",]
    list_filter = ["date",]
    fields = ["created_at", "date", "orders"]
    readonly_fields = ["created_at", "updated_at",]
    filter_vertical = ["orders"]

    def change_view(self, request, object_id, form_url='', extra_context=None):
        obj = self.get_object(request, object_id)
        if not obj:
            return
        if '_order_excel_download' in request.POST:
            content, filename = OrderExcelService(obj).generate_xlsx_bytes()
            response = HttpResponse(
                content,
                content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
            response['Content-Disposition'] = f"attachment; filename*=UTF-8''{quote(filename)}"
            return response
        return super().change_view(request, object_id, form_url, extra_context)

    def has_delete_permission(self, request, obj=None):
        return False
