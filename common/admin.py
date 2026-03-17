import logging
from django.contrib import admin, messages
from django.utils.safestring import mark_safe
from django.http import HttpResponseRedirect
from simple_history.admin import SimpleHistoryAdmin
from main.services.label_service import label_service
from .models import (
    BaseInfoProxy,
    ContractorCategoryProxy,
    ContractorProxy,
    OrgStandartProxy,
    ProductOrgStandartProxy,
    ProductCategoryProxy,
    ProductProxy,
    ProductIngredientProxy,
    ProductBestBeforeProxy,
)

logger = logging.getLogger(__name__)


@admin.register(BaseInfoProxy)
class BaseInfoProxyAdmin(SimpleHistoryAdmin):
    list_display = ["name", "address", "short_address", "phone_number",]


@admin.register(ContractorCategoryProxy)
class ContractorCategoryProxyAdmin(SimpleHistoryAdmin):
    list_display = ["name",]


@admin.register(ContractorProxy)
class ContractorProxyAdmin(SimpleHistoryAdmin):
    list_display = ["category", "name", "city", "street", "comment",]
    fieldsets = (
        ("Основное", {
            "fields": ("category", "name")
        }),
        ("Дополнительная информация", {
            "fields": ("city", "street", "comment")
        }),
    )
    search_fields = ["name", "city", "street",]
    list_filter = ["category", "city",]


@admin.register(OrgStandartProxy)
class OrgStandartProxyAdmin(SimpleHistoryAdmin):
    list_display = ["name", "code",]


class ProductOrgStandartProxyInline(admin.TabularInline):
    model = ProductOrgStandartProxy
    fields = ["org_standart",]
    extra = 1


class ProductIngredientProxyInline(admin.TabularInline):
    model = ProductIngredientProxy
    fields = ["ingredient", "weight_grams"]
    extra = 1


class ProductBestBeforeProxyInline(admin.TabularInline):
    model = ProductBestBeforeProxy
    fields = ["days", "description"]
    extra = 1


@admin.register(ProductCategoryProxy)
class ProductCategoryProxyAdmin(admin.ModelAdmin):
    list_display = ["name",]
    search_fields = ["name",]


@admin.register(ProductProxy)
class ProductProxyAdmin(SimpleHistoryAdmin):
    change_form_template = "admin/product_archive_action.html"

    list_display = ["name", "status", "category", "weight", "calories", "protein", "fat", "carbs", "price", "quantity",]
    fieldsets = (
        ("Основное", {
            "fields": ("status", "category", "name")
        }),
        ("Пищевая ценность", {
            "fields": ("weight", "calories", "protein", "fat", "carbs")
        }),
        ("Цена и количество", {
            "fields": ("price", "quantity")
        }),
    )
    readonly_fields = ["status",]
    search_fields = ["name",]
    list_filter = ["category", "status"]
    inlines = [ProductIngredientProxyInline, ProductBestBeforeProxyInline,]
    actions = None

    def change_view(self, request, object_id, form_url='', extra_context=None):
        obj = self.get_object(request, object_id)
        if not obj:
            return
        if '_archive' in request.POST:
            if obj.status == ProductProxy.ProductStatus.AVAILABLE:
                obj.status = ProductProxy.ProductStatus.ARCHIEVED
                self.message_user(request, f"{obj} отправлен в архив", level=messages.WARNING)
                logger.info(f"{obj} marked as archived")
                obj.save(update_fields=["status"])
                return HttpResponseRedirect(request.path)
        elif '_restore' in request.POST:
            if obj.status == ProductProxy.ProductStatus.ARCHIEVED:
                obj.status = ProductProxy.ProductStatus.AVAILABLE
                self.message_user(request, f"{obj} убран из архива")
                logger.info(f"{obj} moved from archived")
                obj.save(update_fields=["status"])
                return HttpResponseRedirect(request.path)
        return super().change_view(request, object_id, form_url, extra_context)

    @admin.display(description="")
    def barcode_preview(self, obj):
        if not obj.barcode:
            return "(нет штрихкода)"
        return mark_safe(f'<img src="data:image/png;base64,{label_service.generate_barcode_preview_base64(obj.barcode)}" height="80"/>')


@admin.register(ProductIngredientProxy)
class ProductIngredientProxyAdmin(SimpleHistoryAdmin):

    def has_module_permission(self, request):
        return False


@admin.register(ProductBestBeforeProxy)
class ProductBestBeforeProxyAdmin(SimpleHistoryAdmin):

    def has_module_permission(self, request):
        return False
