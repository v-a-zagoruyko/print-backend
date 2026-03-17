import logging
from urllib.parse import quote

from django.contrib import admin, messages
from django.http import HttpResponse, HttpRequest
from django.shortcuts import redirect, render
from simple_history.admin import SimpleHistoryAdmin

from .forms import OrderSupplyForm, OrderSupplyImportForm
from .models import ContractorUser, ContractorOrder, ContractorOrderItem, OrderSupply
from .services.order_excel_service import OrderExcelService
from .services.order_ingredients_excel_service import OrderIngredientsExcelService
from .services.order_supply_import_service import (
    OrderSupplyImportError,
    OrderSupplyImportService,
)

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

    actions = ["import_order_supply_from_excel"]

    def import_order_supply_from_excel(self, request: HttpRequest, queryset):
        """
        Admin action для импорта заявки поставщика из Excel.
        Использует OrderSupplyImportService и показывает результат через admin messages.
        """
        if "apply" in request.POST:
            form = OrderSupplyImportForm(request.POST, request.FILES)
            if form.is_valid():
                uploaded_file = form.cleaned_data["file"]
                service = OrderSupplyImportService(uploaded_file, request.user)
                try:
                    result = service.import_data()
                except OrderSupplyImportError as exc:
                    messages.error(request, str(exc))
                    return None
                except Exception:
                    logger.exception("Unexpected error during OrderSupply import")
                    messages.error(
                        request,
                        "Произошла непредвиденная ошибка при импорте заявки поставщика.",
                    )
                    return None

                msg_parts = [
                    f"Общая заявка на дату {result.order_supply.date.strftime('%d.%m.%Y')} успешно обновлена.",
                    f"Создано заявок контрагентов: {result.created_orders}.",
                    f"Обновлено заявок контрагентов: {result.updated_orders}.",
                    f"Создано позиций: {result.created_items}.",
                    f"Обновлено позиций: {result.updated_items}.",
                ]
                messages.success(request, " ".join(msg_parts))

                if result.missing_barcodes:
                    messages.warning(
                        request,
                        "Следующие штрихкоды не найдены и были пропущены: "
                        + "; ".join(result.missing_barcodes),
                    )

                return None
        else:
            form = OrderSupplyImportForm()

        context = {
            "title": "Импорт заявки поставщика из Excel",
            "form": form,
            "action_checkbox_name": admin.helpers.ACTION_CHECKBOX_NAME,
            "queryset": queryset,
        }
        return render(request, "admin/order_supply_import.html", context)

    import_order_supply_from_excel.short_description = (
        "Импортировать заявку поставщика из Excel"
    )

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
        if '_order_ingredients_excel_download' in request.POST:
            (
                content,
                filename,
                products_missing_workshop,
                products_missing_ingredients,
            ) = OrderIngredientsExcelService(obj).generate_xlsx_with_warnings()
            if products_missing_workshop:
                messages.warning(
                    request,
                    "Следующие товары не были включены в файл ингредиентов, так как у их категорий не указан цех: "
                    + "; ".join(products_missing_workshop),
                )
            if products_missing_ingredients:
                messages.warning(
                    request,
                    "Следующие товары не были включены в файл ингредиентов, так как у них нет ни одной связи с ингредиентами: "
                    + "; ".join(products_missing_ingredients),
                )
            response = HttpResponse(
                content,
                content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
            response['Content-Disposition'] = f"attachment; filename*=UTF-8''{quote(filename)}"
            return response
        return super().change_view(request, object_id, form_url, extra_context)

    def has_delete_permission(self, request, obj=None):
        return False
