from django.urls import reverse
from main.models import Product, Contractor


def admin_has_change_perm(user, model):
    return user.has_perm(f"{model._meta.app_label}.change_{model._meta.model_name}")

def admin_change_url(model, pk):
    return reverse(
        f"admin:{model._meta.app_label}_{model._meta.model_name}_change",
        args=[pk]
    )
