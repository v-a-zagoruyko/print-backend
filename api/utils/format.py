import json
from datetime import datetime, timedelta
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from main.models import BaseInfo, OrgStandart, ContractorCategory

def to_dec(value):
    ZERO_DEC = Decimal('0')
    if value in (None, ''):
        return ZERO_DEC
    try:
        d = Decimal(str(value))
    except (InvalidOperation, ValueError):
        return ZERO_DEC
    d = d.quantize(Decimal('0.1'), rounding=ROUND_HALF_UP)
    if d == d.to_integral():
        return d.to_integral()
    return d

def safe_load_json(val):
    if val in (None, ''):
        return {}
    if isinstance(val, (dict, list)):
        return val
    try:
        return json.loads(val)
    except Exception:
        return {}

def format_nutrition(base):
    calories = to_dec(base.get('calories', 0) or 0)
    protein = to_dec(base.get('protein', 0) or 0)
    fat = to_dec(base.get('fat', 0) or 0)
    carbs = to_dec(base.get('carbs', 0) or 0)
    return f"{calories}К/{protein}Б/{fat}Ж/{carbs}У на 100 гр."

def format_dates(base, now = datetime.now()):
    manufacture = f"Изготовлено: {now.strftime('%d.%m.%y')} 02:00"
    shelf_raw = base.get('shelf_life') or base.get('best_before') or 0
    try:
        shelf_days = int(shelf_raw)
    except Exception:
        shelf_days = 0
    expiry = now + timedelta(days=shelf_days)
    expiry_str = f"Употребить до: {expiry.strftime('%d.%m.%y')} 02:00"
    return manufacture, expiry_str

def format_company_info():
    company = BaseInfo.get_solo()
    return (
        f"Изготовитель: {company.name}<br />"
        f"Адрес производства: {company.address}<br />"
        f"Телефон: {company.phone_number}"
    )

def format_company_short_info():
    company = BaseInfo.get_solo()
    return (
        f"{company.name}<br />"
        f"{company.short_address}"
    )

def extract_org_standarts_from_mapping(instance):
    org_ids_with_index = []
    if isinstance(instance, dict):
        for k, v in instance.items():
            if k.startswith('org_standart-') and k.endswith('-org_standart'):
                parts = k.split('-')
                try:
                    idx = int(parts[1])
                except Exception:
                    continue
                if v not in (None, ''):
                    org_ids_with_index.append((idx, str(v)))
    org_ids_with_index.sort()
    ids = [oid for _, oid in org_ids_with_index]
    if not ids:
        return []
    objs = OrgStandart.objects.filter(pk__in=ids)
    obj_map = {str(o.pk): o for o in objs}
    org_strings = []
    for oid in ids:
        obj = obj_map.get(str(oid))
        if obj:
            org_strings.append(f"{obj.name} СТО {obj.code}")
    return org_strings

def extract_org_standarts_from_instance(instance):
    org_strings = []
    if hasattr(instance, 'org_standart'):
        rel_qs = instance.org_standart.select_related('org_standart').all()
        for rel in rel_qs:
            o = getattr(rel, 'org_standart', None)
            if o:
                org_strings.append(f"{o.name} СТО {o.code}")
    return org_strings

def extract_contractor_from_mapping(instance):
    contractor_id = None
    if isinstance(instance, dict):
        for k, v in instance.items():
            if k == 'category':
                try:
                    idx = int(v)
                except Exception:
                    continue
                if v not in (None, ''):
                    contractor_id = str(v)
    if not contractor_id:
        return ""
    contractor_obj = ContractorCategory.objects.filter(pk=contractor_id)
    if contractor_obj.exists():
        return contractor_obj.first().name
    return ""

def extract_contractor_from_instance(instance):
    contractor = ""
    if hasattr(instance, 'category'):
        contractor = instance.category.name
    return contractor
