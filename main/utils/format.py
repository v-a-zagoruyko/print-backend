from django.utils import timezone
from datetime import datetime, timedelta
from decimal import Decimal, InvalidOperation
from main.models import BaseInfo

def to_dec(value):
    ZERO_DEC = Decimal('0')
    if value in (None, ''):
        return ZERO_DEC
    try:
        d = Decimal(str(value))
    except (InvalidOperation, ValueError):
        return ZERO_DEC
    d = d.quantize(Decimal('0.01'))
    if d == d.to_integral():
        return d.to_integral()
    s = format(d, 'f')
    if '.' in s:
        s = s.rstrip('0').rstrip('.')
    return Decimal(s)

def format_ingredients(base):
    ingredients = base.get('ingredients', '')
    return f"Состав: {ingredients}"

def format_nutrition(base):
    calories = to_dec(base.get('calories', 0) or 0)
    protein = to_dec(base.get('protein', 0) or 0)
    fat = to_dec(base.get('fat', 0) or 0)
    carbs = to_dec(base.get('carbs', 0) or 0)
    return f"{calories}К/{protein}Б/{fat}Ж/{carbs}У на 100 гр."

def format_dates(base, now = None):
    if now is None:
        now = timezone.now()
        now = now + timedelta(days=1)
    else:
        dt_naive = datetime.strptime(now, "%Y-%m-%d")
        now = timezone.make_aware(dt_naive, timezone.get_current_timezone())
    manufacture = f"Изготовлено: {now.strftime('%d.%m.%y')} 02:00"
    shelf_raw = base.get('best_before', 0)
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
