import io
from typing import Dict, List, Set, Tuple

from django.db.models import Prefetch
from django.utils import timezone
import pandas as pd

from main.models import Product, ProductIngredient
from orders.models import ContractorOrder, ContractorOrderItem


class OrderIngredientsExcelService:
    FONT_NAME = "Times New Roman"
    FONT_SIZE = 13

    COL_NAME_WIDTH = 30
    COL_QTY_WIDTH = 12
    COL_TOTAL_WIDTH = 22
    COL_INGREDIENT_WIDTH = 25
    COL_INGREDIENT_QTY_WIDTH = 15

    HEADERS = [
        "Наименование",
        "Количество",
        "Общее необходимое кол-во начинки, кг",
        "Начинка",
        "Кол-во, кг",
    ]

    def __init__(self, order_supply):
        self.order_supply = order_supply

    def _collect_data(self) -> Tuple[Dict, List[str], List[str]]:
        orders_qs = (
            self.order_supply.orders
            .exclude(status=ContractorOrder.Status.CANCELLED)
            .prefetch_related(
                Prefetch(
                    "order_items",
                    queryset=ContractorOrderItem.objects.only("product_id", "quantity"),
                )
            )
            .all()
        )

        product_qty_totals: Dict[int, int] = {}
        for order in orders_qs:
            for item in order.order_items.all():
                product_qty_totals[item.product_id] = (
                    product_qty_totals.get(item.product_id, 0) + item.quantity
                )

        if not product_qty_totals:
            return {}, [], []

        products_qs = (
            Product.objects
            .filter(pk__in=product_qty_totals.keys())
            .select_related("category__workshop")
            .prefetch_related(
                Prefetch(
                    "product_ingredients",
                    queryset=ProductIngredient.objects.select_related("ingredient").order_by("ingredient__name"),
                )
            )
        )

        workshop_data: Dict[str, List[Tuple]] = {}
        products_missing_workshop: Set[str] = set()
        products_missing_ingredients: Set[str] = set()

        for prod in products_qs:
            ingredients = list(prod.product_ingredients.all())
            if not ingredients:
                products_missing_ingredients.add(prod.name)
                continue

            workshop = prod.category.workshop if prod.category else None
            if workshop is None:
                products_missing_workshop.add(prod.name)
                continue

            total_qty = product_qty_totals[prod.pk]
            workshop_data.setdefault(workshop.name, []).append((prod, total_qty))

        for wname in workshop_data:
            workshop_data[wname].sort(key=lambda x: x[0].name)

        return (
            workshop_data,
            sorted(products_missing_workshop),
            sorted(products_missing_ingredients),
        )

    def _create_formats(self, workbook):
        header_format = workbook.add_format({
            "font_name": self.FONT_NAME,
            "font_size": self.FONT_SIZE,
            "bold": True,
            "text_wrap": True,
            "valign": "center",
            "align": "center",
            "border": 1,
        })
        text_format = workbook.add_format({
            "font_name": self.FONT_NAME,
            "font_size": self.FONT_SIZE,
            "text_wrap": True,
            "valign": "top",
            "border": 1,
        })
        number_format = workbook.add_format({
            "font_name": self.FONT_NAME,
            "font_size": self.FONT_SIZE,
            "valign": "top",
            "num_format": "0",
            "border": 1,
        })
        kg_format = workbook.add_format({
            "font_name": self.FONT_NAME,
            "font_size": self.FONT_SIZE,
            "valign": "top",
            "num_format": "0.000",
            "border": 1,
        })
        return {"header": header_format, "text": text_format, "number": number_format, "kg": kg_format}

    def _write_sheet(self, writer, formats, products_with_qty: List[Tuple], sheet_name: str):
        # Build groups: [(prod_name, qty, [(weight_kg, ingredient_name, total_kg), ...])]
        groups = []
        for prod, total_qty in products_with_qty:
            ingredient_rows = [
                (
                    round(pi.weight_grams / 1000, 3),
                    pi.ingredient.name,
                    round(total_qty * pi.weight_grams / 1000, 3),
                )
                for pi in prod.product_ingredients.all()
            ]
            if ingredient_rows:
                groups.append((prod.name, total_qty, ingredient_rows))

        # Build flat rows for DataFrame (to use to_excel for sheet creation)
        flat_rows = []
        for prod_name, qty, ing_rows in groups:
            for weight_kg, ing_name, total_kg in ing_rows:
                flat_rows.append([prod_name, qty, weight_kg, ing_name, total_kg])

        df = pd.DataFrame(flat_rows, columns=self.HEADERS)
        df.to_excel(writer, index=False, sheet_name=sheet_name)
        worksheet = writer.sheets[sheet_name]

        col_widths = [
            self.COL_NAME_WIDTH,
            self.COL_QTY_WIDTH,
            self.COL_TOTAL_WIDTH,
            self.COL_INGREDIENT_WIDTH,
            self.COL_INGREDIENT_QTY_WIDTH,
        ]
        for col_idx, width in enumerate(col_widths):
            worksheet.set_column(col_idx, col_idx, width)
            worksheet.write(0, col_idx, self.HEADERS[col_idx], formats["header"])

        # Write data with merged cells for cols 0 and 1 per product
        excel_row = 1  # 0-indexed, row 0 is header
        for prod_name, qty, ing_rows in groups:
            n = len(ing_rows)
            last_row = excel_row + n - 1

            if n > 1:
                worksheet.merge_range(excel_row, 0, last_row, 0, prod_name, formats["text"])
                worksheet.merge_range(excel_row, 1, last_row, 1, qty, formats["number"])
            else:
                worksheet.write(excel_row, 0, prod_name, formats["text"])
                worksheet.write(excel_row, 1, qty, formats["number"])

            for i, (weight_kg, ing_name, total_kg) in enumerate(ing_rows):
                row = excel_row + i
                worksheet.write(row, 2, weight_kg, formats["kg"])
                worksheet.write(row, 3, ing_name, formats["text"])
                worksheet.write(row, 4, total_kg, formats["kg"])

            excel_row += n

        worksheet.freeze_panes(1, 0)

    def generate_xlsx_with_warnings(self) -> Tuple[bytes, str, List[str], List[str]]:
        workshop_data, products_missing_workshop, products_missing_ingredients = (
            self._collect_data()
        )

        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
            formats = self._create_formats(writer.book)

            if workshop_data:
                for workshop_name in sorted(workshop_data.keys()):
                    self._write_sheet(
                        writer, formats, workshop_data[workshop_name], workshop_name[:31]
                    )
            else:
                pd.DataFrame(columns=self.HEADERS).to_excel(
                    writer, index=False, sheet_name="Ингредиенты"
                )

        buffer.seek(0)
        date = getattr(self.order_supply, "date", timezone.localdate())
        date_str = date.strftime("%d.%m.%Y")
        filename = f"Заявка ингредиенты на {date_str}.xlsx"

        return buffer.getvalue(), filename, products_missing_workshop, products_missing_ingredients
