import logging
from django.contrib import admin, messages
from django.utils.safestring import mark_safe
from django.db.models import JSONField
from django.http import HttpResponseRedirect
from django_celery_beat import models
from django_json_widget.widgets import JSONEditorWidget
from simple_history.admin import SimpleHistoryAdmin
from .utils.admin import ProductTemplateFilter, generate_barcode
from .models import BaseInfo, Template, OrgStandart, ContractorCategory, ContractorTemplate, Contractor, Product, ProductCategory, ProductTemplate, ProductOrgStandart

logger = logging.getLogger(__name__)

admin.site.index_title = "Панель управления"


@admin.register(BaseInfo)
class BaseInfoAdmin(SimpleHistoryAdmin):
    list_display = ["name", "address", "short_address", "phone_number",]


@admin.register(Template)
class TemplateAdmin(SimpleHistoryAdmin):
    list_display = ["name", "width", "height",]
    fields = ["name", "width", "height", "elements", "label_preview",]
    readonly_fields = ["label_preview",]
    formfield_overrides = {
        JSONField: {'widget': JSONEditorWidget},
    }

    @admin.display(description="Этикетка")
    def label_preview(self, obj):
        return mark_safe("""
        <div style="display: flex; flex-direction: column; gap: 4px;">
            <div id="label-preview-container"></div>
        </div>""")

    class Media:
        js = (
            'js/template_preview.js',
        )


@admin.register(OrgStandart)
class OrgStandartAdmin(SimpleHistoryAdmin):
    list_display = ["name", "code",]


@admin.register(ContractorCategory)
class ContractorCategoryAdmin(SimpleHistoryAdmin):
    list_display = ["name",]


class ContractorTemplateInline(admin.TabularInline):
    model = ContractorTemplate
    fields = ["template",]
    extra = 1
    max_num = 1


@admin.register(Contractor)
class ContractorAdmin(SimpleHistoryAdmin):
    list_display = ["category", "name", "city", "street", "comment",]
    fieldsets = (
        ("Шаблон этикетки", {
            "fields": ("label_preview",)
        }),
        ("Основное", {
            "fields": ("category", "name")
        }),
        ("Дополнительная информация", {
            "fields": ("city", "street", "comment")
        }),
    )
    readonly_fields = ["label_preview",]
    search_fields = ["name", "city", "street",]
    list_filter = ["category", "city",]
    inlines = [ContractorTemplateInline,]

    @admin.display(description="Этикетка")
    def label_preview(self, obj):
        return mark_safe("""
        <div style="display: flex; flex-direction: column; gap: 4px;">
            <div id="label-preview-container"></div>
        </div>""")

    class Media:
        js = (
            'js/generate_label.js',
            'js/contractor_template_preview.js',
        )


class ProductTemplateInline(admin.TabularInline):
    model = ProductTemplate
    fields = ["template",]
    extra = 1
    min_num = 1
    max_num = 1


class ProductOrgStandartInline(admin.TabularInline):
    model = ProductOrgStandart
    fields = ["org_standart",]
    extra = 1


@admin.register(ProductCategory)
class ProductCategoryAdmin(admin.ModelAdmin):
    list_display = ["name",]
    search_fields = ["name",]


@admin.register(Product)
class ProductAdmin(SimpleHistoryAdmin):
    change_form_template = "admin/product_archive_action.html"

    list_display = ["name", "status", "entity_template", "category", "weight", "calories", "protein", "fat", "carbs", "barcode_preview",]
    fieldsets = (
        ("Шаблон этикетки", {
            "fields": ("label_preview",)
        }),
        ("Основное", {
            "fields": ("status", "category", "name")
        }),
        ("Состав и информация", {
            "fields": ("ingredients", "caption", "best_before")
        }),
        ("Питательная ценность", {
            "fields": ("weight", "calories", "fat", "protein", "carbs")
        }),
        ("Штрихкод", {
            "fields": ("barcode", "barcode_preview")
        }),
    )
    readonly_fields = ["status", "barcode_preview", "label_preview",]
    search_fields = ["name", "barcode",]
    list_filter = ["category", "status", ProductTemplateFilter,]
    inlines = [ProductOrgStandartInline, ProductTemplateInline,]
    actions = None

    def change_view(self, request, object_id, form_url='', extra_context=None):
        obj = self.get_object(request, object_id)
        if not obj:
            return
        if '_archive' in request.POST:
            if obj.status == Product.ProductStatus.AVAILABLE:
                obj.status = Product.ProductStatus.ARCHIEVED
                self.message_user(request, f"{obj} отправлен в архив", level=messages.WARNING)
                logger.info(f"{obj} marked as archived")
                obj.save(update_fields=["status"])
                return HttpResponseRedirect(request.path)
        elif '_restore' in request.POST:
            if obj.status == Product.ProductStatus.ARCHIEVED:
                obj.status = Product.ProductStatus.AVAILABLE
                self.message_user(request, f"{obj} убран из архива")
                logger.info(f"{obj} moved from archived")
                obj.save(update_fields=["status"])
                return HttpResponseRedirect(request.path)
        return super().change_view(request, object_id, form_url, extra_context)

    @admin.display(description="Шаблон")
    def entity_template(self, obj):
        if not obj.entity_template:
            return "-"
        return obj.entity_template.template.name

    @admin.display(description="")
    def barcode_preview(self, obj):
        if not obj.barcode:
            return "(нет штрихкода)"
        return mark_safe(f'<img src="data:image/png;base64,{generate_barcode(obj.barcode)}" height="80"/>')

    @admin.display(description="Этикетка")
    def label_preview(self, obj):
        return mark_safe("""
        <div style="display: flex; flex-direction: column; gap: 4px;">
            <div id="label-preview-container"></div>
        </div>""")

    class Media:
        js = (
            'js/generate_label.js',
            'js/product_template_preview.js',
        )