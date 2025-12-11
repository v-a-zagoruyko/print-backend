import re
from django.core.management.base import BaseCommand
from django.db import transaction
from main.models import Contractor

class Command(BaseCommand):
    help = "Убрать префикс 'г. ' в поле city у всех Contractor."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            dest="dry_run",
            help="Не сохранять изменения, только показать статистику",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        pattern = re.compile(r'^\s*г\.?\s+', re.IGNORECASE)
        qs = Contractor.objects.all()
        total = qs.count()
        changed = 0
        skipped = 0
        errors = 0

        with transaction.atomic():
            for obj in qs:
                original = obj.city or ""
                new = pattern.sub("", original).strip()
                if new != original:
                    if dry_run:
                        changed += 1
                        continue
                    obj.city = new
                    try:
                        obj.save(update_fields=["city"])
                        changed += 1
                    except Exception:
                        errors += 1
                else:
                    skipped += 1

        self.stdout.write(self.style.SUCCESS("Нормализация городов завершена"))
        self.stdout.write(f"Всего записей: {total}")
        self.stdout.write(f"Изменено: {changed}")
        self.stdout.write(f"Пропущено (без изменений): {skipped}")
        self.stdout.write(f"Ошибок при сохранении: {errors}")
        if dry_run:
            self.stdout.write(self.style.WARNING("Dry run — изменений в БД не вносилось"))
