from django.core.management.base import BaseCommand
from django.db import transaction
import sqlite3
import os
from main.models import Product, OrgStandart, ProductOrgStandart

class Command(BaseCommand):
    help = "Заполнить ProductOrgStandart по данным CTO из старой SQLite базы."

    def add_arguments(self, parser):
        parser.add_argument(
            "--old-db",
            dest="old_db",
            default="./db.sqlite3",
            help="Путь до файла старой SQLite базы (по умолчанию ./db.sqlite3)",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            dest="dry_run",
            help="Не сохранять в БД, только показать что бы было сделано",
        )

    def handle(self, *args, **options):
        old_db_path = options["old_db"]
        dry_run = options["dry_run"]

        if not os.path.exists(old_db_path):
            self.stderr.write(self.style.ERROR(f"Файл {old_db_path} не найден"))
            return

        conn = sqlite3.connect(old_db_path)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()

        cur.execute("SELECT id, name FROM main_product")
        old_products = cur.fetchall()
        old_prod_name_by_id = {r["id"]: (r["name"] or "").strip() for r in old_products}

        cur.execute("SELECT id, code FROM main_cto")
        old_ctos = cur.fetchall()
        old_cto_code_by_id = {r["id"]: (r["code"] or "").strip() for r in old_ctos}

        cur.execute("SELECT product_id, cto_id FROM main_product_cto")
        links = cur.fetchall()

        conn.close()

        processed = 0
        created = 0
        skipped_no_product = 0
        skipped_no_org = 0
        skipped_exists = 0
        errors = 0
        created_rows = []

        with transaction.atomic():
            for r in links:
                processed += 1
                old_pid = r["product_id"]
                old_ctoid = r["cto_id"]
                pname = old_prod_name_by_id.get(old_pid, "").strip()
                cto_code = old_cto_code_by_id.get(old_ctoid, "").strip()
                if not pname:
                    skipped_no_product += 1
                    continue
                if not cto_code:
                    skipped_no_org += 1
                    continue
                new_prod = Product.objects.filter(name__exact=pname).first()
                if not new_prod:
                    skipped_no_product += 1
                    continue
                org = OrgStandart.objects.filter(code__exact=cto_code).first()
                if not org:
                    skipped_no_org += 1
                    continue
                exists = ProductOrgStandart.objects.filter(product=new_prod, org_standart=org).exists()
                if exists:
                    skipped_exists += 1
                    continue
                try:
                    if dry_run:
                        created += 1
                        created_rows.append((new_prod.id, new_prod.name, org.id, org.code))
                        continue
                    ProductOrgStandart.objects.create(product=new_prod, org_standart=org)
                    created += 1
                    created_rows.append((new_prod.id, new_prod.name, org.id, org.code))
                except Exception:
                    errors += 1
                    continue

        self.stdout.write(self.style.SUCCESS("populate_products_org_standarts завершён"))
        self.stdout.write(f"Ссылок (M2M) в старой БД: {processed}")
        self.stdout.write(f"Связей создано: {created}")
        self.stdout.write(f"Пропущено (нет продукта в новой БД): {skipped_no_product}")
        self.stdout.write(f"Пропущено (нет OrgStandart по code): {skipped_no_org}")
        self.stdout.write(f"Пропущено (уже существует): {skipped_exists}")
        self.stdout.write(f"Ошибок при добавлении: {errors}")
        if created_rows:
            self.stdout.write("Примеры созданных связей (product_id, product_name, org_id, org_code):")
            for row in created_rows[:20]:
                self.stdout.write(str(row))
        if dry_run:
            self.stdout.write(self.style.WARNING("Dry run — изменений в БД не вносилось"))
