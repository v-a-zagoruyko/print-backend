from rest_framework import serializers
from main.models import Product, Contractor
from .utils.format import (
    to_dec,
    safe_load_json,
    format_nutrition,
    format_dates,
    format_company_info,
    format_company_short_info,
    extract_org_standarts_from_mapping,
    extract_org_standarts_from_instance,
    extract_contractor_from_mapping,
    extract_contractor_from_instance
)


class ProductRepresentationMixin:
    def build_product_representation(self, base, instance=None):
        result = {
            "name": base.get('name', "") or "",
            "weight": base.get('weight', "") or "",
            "caption": base.get('caption', "") or "",
            "ingredients": base.get('ingredients', "") or "",
            "barcode": base.get('barcode', "1111111111111"),
        }
        result['nutrition'] = format_nutrition(base)
        manufacture, expiry = format_dates(base)
        result['manufacture_date'] = manufacture
        result['expiry_date'] = expiry
        if instance is None:
            orgs = extract_org_standarts_from_mapping(base if isinstance(base, dict) else {})
        else:
            if isinstance(instance, dict):
                orgs = extract_org_standarts_from_mapping(instance)
            else:
                orgs = extract_org_standarts_from_instance(instance)
        result['org_standarts'] = ", ".join(orgs)
        result['company_info'] = format_company_info()
        return result


class ContractorRepresentationMixin:
    def build_contractor_representation(self, base, instance=None):
        result = {
            "name": base.get('name', ""),
            "city": f"г. {base.get('city', '')}",
            "street": base.get('street', ""),
            "comment": base.get('comment', ""),
        }
        if instance is None:
            contractor = extract_contractor_from_mapping(base if isinstance(base, dict) else {})
        else:
            if isinstance(instance, dict):
                contractor = extract_contractor_from_mapping(instance)
            else:
                contractor = extract_contractor_from_instance(instance)
        result['contractor'] = contractor
        result['company_short_info'] = format_company_short_info()
        return result

class TemplatePayloadSerializer(serializers.Serializer):
    width = serializers.DecimalField(max_digits=4, decimal_places=1, required=False)
    height = serializers.DecimalField(max_digits=4, decimal_places=1, required=False)
    elements = serializers.JSONField(required=False)

    def to_representation(self, instance):
        base = super().to_representation(instance)
        return {
            "width": to_dec(base.get('width', 0) or 0),
            "height": to_dec(base.get('height', 0) or 0),
            "elements": safe_load_json(base.get('elements', '{}')),
        }

class ProductPayloadSerializer(serializers.Serializer, ProductRepresentationMixin):
    name = serializers.CharField(required=False, allow_blank=True)
    ingredients = serializers.CharField(required=False, allow_blank=True)
    weight = serializers.CharField(required=False, allow_blank=True)
    calories = serializers.DecimalField(max_digits=6, decimal_places=2, required=False)
    protein = serializers.DecimalField(max_digits=6, decimal_places=2, required=False)
    fat = serializers.DecimalField(max_digits=6, decimal_places=2, required=False)
    carbs = serializers.DecimalField(max_digits=6, decimal_places=2, required=False)
    barcode = serializers.CharField(required=False, allow_blank=True)
    caption = serializers.CharField(required=False, allow_blank=True)
    best_before = serializers.IntegerField(required=False)

    def to_representation(self, instance):
        base = super().to_representation(instance)
        return self.build_product_representation(base, instance)

class ProductModelSerializer(serializers.ModelSerializer, ProductRepresentationMixin):
    class Meta:
        model = Product
        fields = '__all__'

    def to_representation(self, instance):
        base = super().to_representation(instance)
        return self.build_product_representation(base, instance)

class ProductLabelListSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    category = serializers.CharField()

class ProductLabelSerializer(serializers.Serializer):
    name = serializers.CharField()
    category = serializers.CharField()
    pdf = serializers.CharField()

class ContractorPayloadSerializer(serializers.Serializer, ContractorRepresentationMixin):
    name = serializers.CharField(required=False, allow_blank=True)
    city = serializers.CharField(required=False, allow_blank=True)
    street = serializers.CharField(required=False, allow_blank=True)
    comment = serializers.CharField(required=False, allow_blank=True)

    def to_representation(self, instance):
        base = super().to_representation(instance)
        return self.build_contractor_representation(base, instance)

class ContractorModelSerializer(serializers.ModelSerializer, ProductRepresentationMixin):
    class Meta:
        model = Contractor
        fields = '__all__'

    def to_representation(self, instance):
        base = super().to_representation(instance)
        return self.build_contractor_representation(base, instance)

class ContractorLabelListSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    street = serializers.CharField()
    category = serializers.CharField()

class ContractorLabelSerializer(serializers.Serializer):
    name = serializers.CharField()
    category = serializers.CharField()
    pdf = serializers.CharField()
