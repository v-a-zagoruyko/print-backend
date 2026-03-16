import io
from typing import Dict, List, Tuple

import pandas as pd
from django.db.models import Prefetch
from django.utils import timezone
from xlsxwriter.utility import xl_col_to_name

from main.models import ProductIngredient
from orders.models import ContractorOrder, ContractorOrderItem


class OrderIngredientsExcelService:
    FIRST_COL_WIDTH = 32
    OTHER_COL_WIDTH = 18
    FONT_NAME = "Times New Roman"
    FONT_SIZE = 13

    def __init__(self, order_supply):
        self.order_supply = order_supply

    def _collect_aggregated_data(
        self,
    ) -> Tuple[
        Dict[str, Dict[str, int]],
        List[str],
        List[str],
    ]:
        orders_qs = (
            self.order_supply.orders.exclude(status=ContractorOrder.Status.CANCELLED)
            .select_related("contractor_user__contractor")
            .prefetch_related(
                Prefetch(
                    "order_items",
                    queryset=ContractorOrderItem.objects.select_related(
                        "product__category__workshop"
                    ).prefetch_related(
                        Prefetch(
                            "product__product_ingredients",
                            queryset=ProductIngredient.objects.select_related(
                                "ingredient"
                            ),
                        )
                    ),
                )
            )
            .all()
        )

        data: Dict[str, Dict[str, int]] = {}
        products_missing_workshop: List[str] = []
        products_missing_ingredients: List[str] = []

        for order in orders_qs:
            for item in order.order_items.all():
                product = item.product
                category = getattr(product, "category", None)
                workshop = getattr(category, "workshop", None)

                product_name = getattr(product, "name", None) or str(product)

                if workshop is None:
                    products_missing_workshop.append(product_name)
                    continue

                product_ingredients = list(product.product_ingredients.all())
                if not product_ingredients:
                    products_missing_ingredients.append(product_name)
                    continue

                workshop_name = workshop.name
                workshop_data = data.setdefault(workshop_name, {})

                for pi in product_ingredients:
                    ingredient_name = pi.ingredient.name
                    total_weight_grams = int(pi.weight_grams) * int(item.quantity)
                    workshop_data[ingredient_name] = (
                        workshop_data.get(ingredient_name, 0) + total_weight_grams
                    )

        products_missing_workshop = sorted(set(products_missing_workshop))
        products_missing_ingredients = sorted(set(products_missing_ingredients))

        return data, products_missing_workshop, products_missing_ingredients

    def _create_formats(self, workbook):
        header_format = workbook.add_format(
            {
                "font_name": self.FONT_NAME,
                "font_size": self.FONT_SIZE,
                "bold": True,
                "text_wrap": True,
                "valign": "center",
                "align": "center",
            }
        )
        text_format = workbook.add_format(
            {
                "font_name": self.FONT_NAME,
                "font_size": self.FONT_SIZE,
                "text_wrap": True,
                "valign": "top",
            }
        )
        number_format = workbook.add_format(
            {
                "font_name": self.FONT_NAME,
                "font_size": self.FONT_SIZE,
                "valign": "top",
                "num_format": "0",
            }
        )
        total_header_format = workbook.add_format(
            {
                "font_name": self.FONT_NAME,
                "font_size": self.FONT_SIZE,
                "bold": True,
                "text_wrap": True,
                "valign": "center",
                "align": "center",
                "bg_color": "#F2F2F2",
                "border": 1,
            }
        )
        total_number_format = workbook.add_format(
            {
                "font_name": self.FONT_NAME,
                "font_size": self.FONT_SIZE,
                "valign": "top",
                "num_format": "0",
                "bold": True,
                "border": 1,
            }
        )
        return {
            "header": header_format,
            "text": text_format,
            "number": number_format,
            "total_header": total_header_format,
            "total_number": total_number_format,
        }

    def _write_table(self, worksheet, df: pd.DataFrame, formats):
        nrows = len(df)
        ncols = len(df.columns)

        for col_idx, col_name in enumerate(df.columns):
            width = self.FIRST_COL_WIDTH if col_idx == 0 else self.OTHER_COL_WIDTH
            worksheet.set_column(col_idx, col_idx, width)
            worksheet.write(0, col_idx, col_name or "", formats["header"])

        for row_idx in range(1, nrows + 1):
            for col_idx in range(0, ncols):
                value = df.iloc[row_idx - 1, col_idx]
                if col_idx == 0:
                    worksheet.write(row_idx, col_idx, value, formats["text"])
                else:
                    worksheet.write(row_idx, col_idx, value, formats["number"])

    def _write_total_column(self, worksheet, df: pd.DataFrame, formats):
        nrows = len(df)
        ncols = len(df.columns)
        total_col_idx = ncols
        worksheet.set_column(total_col_idx, total_col_idx, self.OTHER_COL_WIDTH)
        worksheet.write(0, total_col_idx, "Общий вес, г", formats["total_header"])

        first_data_col = 1
        last_data_col = ncols - 1 if ncols - 1 >= first_data_col else first_data_col

        for row_idx in range(1, nrows + 1):
            start_col_letter = xl_col_to_name(first_data_col)
            end_col_letter = xl_col_to_name(last_data_col)
            excel_row = row_idx + 1
            formula = f"=SUM({start_col_letter}{excel_row}:{end_col_letter}{excel_row})"
            worksheet.write_formula(row_idx, total_col_idx, formula, formats["total_number"])

    def generate_xlsx_with_warnings(
        self,
    ) -> Tuple[bytes, str, List[str], List[str]]:
        data, products_missing_workshop, products_missing_ingredients = (
            self._collect_aggregated_data()
        )

        buffer = io.BytesIO()

        with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
            workbook = writer.book
            formats = self._create_formats(workbook)

            if data:
                for workshop_name in sorted(data.keys()):
                    ingredients_map = data[workshop_name]
                    rows = []
                    for ingredient_name in sorted(ingredients_map.keys()):
                        rows.append(
                            {
                                "Ингредиент": ingredient_name,
                                "Вес, г": int(ingredients_map[ingredient_name]),
                            }
                        )
                    df = pd.DataFrame(rows)
                    sheet_name = workshop_name[:31] or "Цех"
                    df.to_excel(writer, index=False, sheet_name=sheet_name)
                    worksheet = writer.sheets[sheet_name]
                    self._write_table(worksheet, df, formats)
            else:
                df_empty = pd.DataFrame(columns=["Ингредиент", "Вес, г"])
                sheet_name = "Ингредиенты"
                df_empty.to_excel(writer, index=False, sheet_name=sheet_name)
                worksheet = writer.sheets[sheet_name]
                self._write_table(worksheet, df_empty, formats)

        buffer.seek(0)
        date = getattr(self.order_supply, "date", timezone.localdate())
        date_str = date.strftime("%d.%m.%Y")
        filename = f"Заявка ингредиенты на {date_str}.xlsx"

        return (
            buffer.getvalue(),
            filename,
            products_missing_workshop,
            products_missing_ingredients,
        )

