import re
from django.core.management.base import BaseCommand
from django.db import transaction
from main.models import Product

class Command(BaseCommand):
    help = "Обновить поле caption у всех записей в модели Product"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            dest="dry_run",
            help="Не сохранять изменения, только показать статистику",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        qs = Product.objects.all()
        total = qs.count()
        changed = 0
        skipped = 0
        errors = 0

        with transaction.atomic():
            for obj in qs:
                original = obj.caption or ""
                new = "Хранить при температуре от 0 до +6°С. Продукция может содержать аллергены: сельдерей, соя, арахис, орехи, рыба, морепродукты, пшеница."
                if new != original:
                    if dry_run:
                        changed += 1
                        continue
                    obj.caption = new
                    try:
                        obj.save(update_fields=["caption"])
                        changed += 1
                    except Exception:
                        errors += 1
                else:
                    skipped += 1

        self.stdout.write(self.style.SUCCESS("Обновление caption завершено"))
        self.stdout.write(f"Всего записей: {total}")
        self.stdout.write(f"Изменено: {changed}")
        self.stdout.write(f"Пропущено (без изменений): {skipped}")
        self.stdout.write(f"Ошибок при сохранении: {errors}")
        if dry_run:
            self.stdout.write(self.style.WARNING("Dry run — изменений в БД не вносилось"))
