import json
from main.models import Template, OrgStandart, ContractorCategory

def extract_json(val):
    if val in (None, ''):
        return {}
    if isinstance(val, (dict, list)):
        return val
    try:
        return json.loads(val)
    except Exception:
        return {}

def extract_template_from_mapping(instance):
    templates_with_index = []
    if isinstance(instance, dict):
        for k, v in instance.items():
            if k.startswith('product_template-') and k.endswith('-template') or k.startswith('contractor_template-') and k.endswith('-template'):
                parts = k.split('-')
                try:
                    idx = int(parts[1])
                except Exception:
                    continue
                if v not in (None, ''):
                    templates_with_index.append((idx, str(v)))
    templates_with_index.sort()
    ids = [oid for _, oid in templates_with_index]
    if not ids:
        return []
    return Template.objects.get(pk=ids[0])

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
            org_strings.append(f"СТО {obj.code}")
    return org_strings

def extract_org_standarts_from_instance(instance):
    org_strings = []
    if hasattr(instance, 'org_standart'):
        rel_qs = instance.org_standart.select_related('org_standart').all()
        for rel in rel_qs:
            o = getattr(rel, 'org_standart', None)
            if o:
                org_strings.append(f"СТО {o.code}")
    return org_strings


def extract_best_before_from_mapping(instance):
    """
    Собирает строку срока годности из данных формы Django admin.

    Ожидает ключи вида:
    - best_before_options-<idx>-days
    - best_before_options-<idx>-description
    """
    if not isinstance(instance, dict):
        return ""

    items_by_index = {}
    for k, v in instance.items():
        if not isinstance(k, str):
            continue
        if not k.startswith("best_before_options-"):
            continue
        parts = k.split("-")
        if len(parts) < 3:
            continue
        try:
            idx = int(parts[1])
        except Exception:
            continue
        field = parts[2]
        if field not in ("days", "description"):
            continue
        if idx not in items_by_index:
            items_by_index[idx] = {"days": None, "description": ""}
        items_by_index[idx][field] = v

    lines = []
    for idx in sorted(items_by_index.keys()):
        item = items_by_index[idx]
        days_raw = item.get("days")
        desc = (item.get("description") or "").strip()
        try:
            days = int(days_raw) if days_raw not in (None, "") else None
        except Exception:
            days = None
        if days is None and not desc:
            continue
        if days is None:
            continue
        line = f"{days} суток {desc}".strip()
        lines.append(line)

    if not lines:
        return ""
    return f"Срок годности: {', '.join(lines)}"


def extract_best_before_from_instance(instance):
    """
    Собирает строку срока годности из связей Product.best_before_options.
    """
    if not hasattr(instance, "best_before_options"):
        return ""

    lines = []
    qs = instance.best_before_options.all()
    for o in qs:
        days = getattr(o, "days", None)
        desc = (getattr(o, "description", "") or "").strip()
        if days is None:
            continue
        line = f"{days} суток {desc}".strip()
        lines.append(line)

    if not lines:
        return ""
    return f"Срок годности: {', '.join(lines)}"

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
