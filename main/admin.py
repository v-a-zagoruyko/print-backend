import logging
from django.contrib import admin, messages
from django.utils.safestring import mark_safe
from django.db.models import JSONField
from django_celery_beat import models
from django_json_widget.widgets import JSONEditorWidget
from simple_history.admin import SimpleHistoryAdmin
from .utils.admin import generate_barcode
from .models import BaseInfo, Template, OrgStandart, ContractorCategory, Contractor, Product, ProductCategory, ProductOrgStandart

logger = logging.getLogger(__name__)

admin.site.site_header = "Администрирование"
admin.site.site_title = "Администрирование"
admin.site.index_title = "Панель управления"
admin.site.site_url = "https://печать.большие-молодцы.рф"


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


@admin.register(Contractor)
class ContractorAdmin(SimpleHistoryAdmin):
    list_display = ["category", "name", "city", "street", "comment",]
    fieldsets = (
        ("Шаблон этикетки", {
            "fields": ("template", "label_preview")
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

    def get_changeform_initial_data(self, request):
        default_template = Template.objects.filter(name="Контрагент")
        if not default_template.exists():
            return {}

        return {
            'template': default_template.first().id
        }

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
    list_display = ["name", "category", "weight", "calories", "protein", "fat", "carbs", "barcode_preview",]
    fieldsets = (
        ("Шаблон этикетки", {
            "fields": ("template", "label_preview")
        }),
        ("Основное", {
            "fields": ("category", "name")
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
    readonly_fields = ["barcode_preview", "label_preview",]
    search_fields = ["name", "barcode",]
    list_filter = ["template__name", "category",]
    inlines = [ProductOrgStandartInline,]

    def get_changeform_initial_data(self, request):
        default_template = Template.objects.filter(name="Большие молодцы")
        if not default_template.exists():
            return {}

        return {
            'template': default_template.first().id
        }

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