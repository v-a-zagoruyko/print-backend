import base64
from io import BytesIO
from django.contrib.admin import SimpleListFilter
from django.urls import reverse
from main.models import Template, Product, Contractor


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

def admin_has_change_perm(user, model):
    return user.has_perm(f"{model._meta.app_label}.change_{model._meta.model_name}")

def admin_change_url(model, pk):
    return reverse(
        f"admin:{model._meta.app_label}_{model._meta.model_name}_change",
        args=[pk]
    )
