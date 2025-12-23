import base64
from django.contrib.admin import SimpleListFilter
from io import BytesIO
from main.models import Template
from barcode import EAN13
from barcode.writer import ImageWriter


class ProductTemplateFilter(SimpleListFilter):
    title = "Шаблон"
    parameter_name = "template"

    def lookups(self, request, model_admin):
        return [
            (t.id, str(t))
            for t in Template.objects.filter(
                product_template__isnull=False
            ).distinct()
        ]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(
                product_template__template_id=self.value()
            )
        return queryset

def generate_barcode(barcode: str) -> str:
    code = barcode[:12]
    buffer = BytesIO()
    writer = ImageWriter()
    writer.dpi = 300
    EAN13(code, writer=writer).write(
        buffer,
        options={
            "quiet_zone": 0,
            "write_text": True,
            "foreground": "black",
            "background": "white",
            "module_width": 0.5,
        },
    )
    return base64.b64encode(buffer.getvalue()).decode()
