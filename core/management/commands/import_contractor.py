from django.core.management.base import BaseCommand
from django.db import transaction
import sqlite3
import os
from main.models import ContractorCategory, Contractor, Template

class Command(BaseCommand):
    help = "Импорт ContractorInfo из старой SQLite базы в текущую DB (Postgres)."

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
            template = Template.objects.get(pk=2)
        except Template.DoesNotExist:
            self.stderr.write(self.style.ERROR("Template с pk=2 не найден в новой базе"))
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

        contractorinfo_table = find_table_guess(tables, "contractorinfo") or find_table_guess(tables, "contractor_info")
        contractor_table = find_table_guess(tables, "contractor")

        if contractorinfo_table and contractor_table and contractorinfo_table == contractor_table:
            others = [t for t in tables if "contractor" in t.lower() and t != contractorinfo_table]
            contractor_table = others[0] if others else contractor_table

        if not contractorinfo_table:
            self.stderr.write(self.style.ERROR("Не нашёл таблицу ContractorInfo в SQLite"))
            conn.close()
            return
        if not contractor_table:
            self.stderr.write(self.style.ERROR("Не нашёл таблицу Contractor (старую) в SQLite"))
            conn.close()
            return

        def table_columns(table_name):
            cur.execute(f"PRAGMA table_info('{table_name}')")
            return [row["name"] for row in cur.fetchall()]

        ci_cols = table_columns(contractorinfo_table)
        c_cols = table_columns(contractor_table)

        def col_lookup(cols, candidates):
            lc = {c.lower(): c for c in cols}
            for cand in candidates:
                if cand.lower() in lc:
                    return lc[cand.lower()]
            return None

        ci_id_col = col_lookup(ci_cols, ["id", "pk"])
        ci_contractor_fk_col = col_lookup(ci_cols, ["contractor_id", "contractor"])
        ci_name_col = col_lookup(ci_cols, ["name", "title", "название"])
        ci_city_col = col_lookup(ci_cols, ["city", "город"])
        ci_street_col = col_lookup(ci_cols, ["street", "улица"])
        ci_company_col = col_lookup(ci_cols, ["company", "компания"])
        c_id_col = col_lookup(c_cols, ["id", "pk"])
        c_name_col = col_lookup(c_cols, ["name", "title", "название"])

        if not ci_contractor_fk_col or not c_id_col or not c_name_col:
            self.stderr.write(self.style.ERROR("В старой БД не нашёл необходимые колонки (contractor FK / contractor.name)"))
            conn.close()
            return

        cur.execute(f"SELECT {c_id_col} as id, {c_name_col} as name FROM '{contractor_table}'")
        old_contractors = cur.fetchall()
        old_contractor_name_by_id = {r["id"]: (r["name"] or "").strip() for r in old_contractors}

        cur.execute(f"SELECT * FROM '{contractorinfo_table}'")
        infos = cur.fetchall()

        created = 0
        skipped_no_cat = 0
        skipped_dup = 0
        errors = 0

        with transaction.atomic():
            for r in infos:
                old_contractor_id = r[ci_contractor_fk_col] if ci_contractor_fk_col in r.keys() else None
                old_contractor_name = old_contractor_name_by_id.get(old_contractor_id, "").strip()
                if not old_contractor_name:
                    skipped_no_cat += 1
                    continue

                category_obj = ContractorCategory.objects.filter(name__exact=old_contractor_name).first()
                if not category_obj:
                    skipped_no_cat += 1
                    continue

                name = (r[ci_name_col] or "").strip() if ci_name_col in r.keys() else ""
                city = (r[ci_city_col] or "").strip() if ci_city_col in r.keys() else ""
                street = (r[ci_street_col] or "").strip() if ci_street_col in r.keys() else ""
                comment = (r[ci_company_col] or "").strip() if ci_company_col in r.keys() else ""

                if not street:
                    street = ""

                if Contractor.objects.filter(name=name, street=street, city=city, category=category_obj).exists():
                    skipped_dup += 1
                    continue

                try:
                    if dry_run:
                        created += 1
                        continue
                    Contractor.objects.create(
                        category=category_obj,
                        name=name or None,
                        city=city or "Тюмень",
                        street=street,
                        comment=comment or None,
                        template=template,
                    )
                    created += 1
                except Exception:
                    errors += 1
                    continue

        conn.close()

        self.stdout.write(self.style.SUCCESS("Импорт ContractorInfo завершён"))
        self.stdout.write(f"Записей ContractorInfo обработано: {len(infos)}")
        self.stdout.write(f"Контракторов в старой БД найдено: {len(old_contractors)}")
        self.stdout.write(f"Записей добавлено: {created}")
        self.stdout.write(f"Пропущено (нет категории/старый contractor пуст): {skipped_no_cat}")
        self.stdout.write(f"Пропущено (дубликаты): {skipped_dup}")
        self.stdout.write(f"Ошибок при добавлении: {errors}")
        if dry_run:
            self.stdout.write(self.style.WARNING("Dry run — изменений в БД не вносилось"))
