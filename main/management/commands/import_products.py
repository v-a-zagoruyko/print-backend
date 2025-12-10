from django.core.management.base import BaseCommand
from django.db import transaction
from decimal import Decimal, InvalidOperation
import sqlite3
import os
from main.models import ProductCategory, Product, Template

class Command(BaseCommand):
    help = "Импорт из старой SQLite базы в текущую DB (Postgres)."

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

        try:
            template = Template.objects.get(pk=1)
        except Template.DoesNotExist:
            self.stderr.write(self.style.ERROR("Template с pk=1 не найден в новой базе"))
            return

        conn = sqlite3.connect(old_db_path)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()

        cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tables = [r["name"] for r in cur.fetchall()]

        def find_table_guess(names, keyword):
            candidates = [t for t in names if keyword in t.lower()]
            if not candidates:
                return None
            exact = [t for t in candidates if t.lower().endswith(f"_{keyword}")]
            if exact:
                return exact[0]
            return sorted(candidates)[0]

        category_table = find_table_guess(tables, "category")
        product_table = find_table_guess(tables, "product")

        if not category_table:
            self.stderr.write(self.style.ERROR("Не нашёл таблицу категорий в SQLite"))
            return
        if not product_table:
            self.stderr.write(self.style.ERROR("Не нашёл таблицу продуктов в SQLite"))
            return

        def table_columns(table_name):
            cur.execute(f"PRAGMA table_info('{table_name}')")
            return [row["name"] for row in cur.fetchall()]

        cat_cols = table_columns(category_table)
        prod_cols = table_columns(product_table)

        def col_lookup(cols, candidates):
            lc = {c.lower(): c for c in cols}
            for cand in candidates:
                if cand.lower() in lc:
                    return lc[cand.lower()]
            return None

        cat_id_col = col_lookup(cat_cols, ["id", "pk"])
        cat_name_col = col_lookup(cat_cols, ["name", "title", "название"])
        if not cat_name_col:
            self.stderr.write(self.style.ERROR("Не нашёл колонку name в таблице категорий"))
            return

        p_id_col = col_lookup(prod_cols, ["id", "pk"])
        p_cat_col = col_lookup(prod_cols, ["category_id", "category", "категория_id", "категория"])
        p_name_col = col_lookup(prod_cols, ["name", "title", "название"])
        p_ingredients_col = col_lookup(prod_cols, ["ingredients", "состав", "ingredient"])
        p_weight_col = col_lookup(prod_cols, ["weight", "вес"])
        p_calories_col = col_lookup(prod_cols, ["calories", "калории"])
        p_protein_col = col_lookup(prod_cols, ["protein", "белки"])
        p_fat_col = col_lookup(prod_cols, ["fat", "жиры"])
        p_carbs_col = col_lookup(prod_cols, ["carbs", "углеводы"])
        p_barcode_col = col_lookup(prod_cols, ["barcode", "штрихкод"])

        if not p_barcode_col or not p_name_col:
            self.stderr.write(self.style.ERROR("В таблице продуктов не нашёл обязательные колонки (barcode/name)"))
            return

        cur.execute(f"SELECT {cat_id_col} as id, {cat_name_col} as name FROM '{category_table}'")
        old_cats = cur.fetchall()

        old_cat_map = {}
        created_cats = 0
        for r in old_cats:
            old_id = r["id"]
            name = (r["name"] or "").strip()
            if not name:
                continue
            existing = ProductCategory.objects.filter(name__iexact=name).first()
            if existing:
                old_cat_map[old_id] = existing
                continue
            if dry_run:
                created = ProductCategory(name=name)
            else:
                created = ProductCategory.objects.create(name=name)
            old_cat_map[old_id] = created
            created_cats += 1

        cur.execute(f"SELECT * FROM '{product_table}'")
        products = cur.fetchall()

        added_products = 0
        skipped_barcode = 0
        skipped_no_cat = 0
        errors = 0

        with transaction.atomic():
            for r in products:
                barcode = (r[p_barcode_col] or "").strip() if p_barcode_col in r.keys() else ""
                if not barcode:
                    skipped_barcode += 1
                    continue
                if Product.objects.filter(barcode=barcode).exists():
                    skipped_barcode += 1
                    continue

                old_cat_id = r[p_cat_col] if p_cat_col in r.keys() else None
                category_obj = old_cat_map.get(old_cat_id)
                if not category_obj:
                    skipped_no_cat += 1
                    continue

                name = (r[p_name_col] or "").strip()
                ingredients = (r[p_ingredients_col] or "").strip() if p_ingredients_col in r.keys() else ""
                weight = (r[p_weight_col] or "").strip() if p_weight_col in r.keys() else ""
                def dec(val):
                    if val is None or str(val).strip() == "":
                        return None
                    try:
                        return Decimal(str(val))
                    except InvalidOperation:
                        return None

                calories = dec(r[p_calories_col]) if p_calories_col in r.keys() else None
                protein = dec(r[p_protein_col]) if p_protein_col in r.keys() else None
                fat = dec(r[p_fat_col]) if p_fat_col in r.keys() else None
                carbs = dec(r[p_carbs_col]) if p_carbs_col in r.keys() else None

                try:
                    if dry_run:
                        added_products += 1
                        continue
                    prod = Product.objects.create(
                        category=category_obj,
                        name=name,
                        ingredients=ingredients,
                        weight=weight,
                        calories=calories if calories is not None else 0,
                        protein=protein if protein is not None else 0,
                        fat=fat if fat is not None else 0,
                        carbs=carbs if carbs is not None else 0,
                        barcode=barcode,
                        template=template,
                    )
                    added_products += 1
                except Exception:
                    errors += 1
                    continue

        conn.close()

        self.stdout.write(self.style.SUCCESS("Импорт завершён"))
        self.stdout.write(f"Категорий найдено в старой БД: {len(old_cats)}")
        self.stdout.write(f"Категорий создано: {created_cats}")
        self.stdout.write(f"Продуктов обработано: {len(products)}")
        self.stdout.write(f"Продуктов добавлено: {added_products}")
        self.stdout.write(f"Пропущено (barcode пустой/существует): {skipped_barcode}")
        self.stdout.write(f"Пропущено (нет категории): {skipped_no_cat}")
        self.stdout.write(f"Ошибок при добавлении: {errors}")
        if dry_run:
            self.stdout.write(self.style.WARNING("Dry run — изменений в БД не вносилось"))
