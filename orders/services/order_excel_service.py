import io
from datetime import datetime
from urllib.parse import quote
from django.utils import timezone
from django.db.models import Prefetch
import pandas as pd
from xlsxwriter.utility import xl_col_to_name
from orders.models import ContractorOrder, ContractorOrderItem


class OrderExcelService:
    FIRST_COL_WIDTH = 22
    OTHER_COL_WIDTH = 18
    TOTAL_COL_WIDTH = 18
    FONT_NAME = 'Times New Roman'
    FONT_SIZE = 13

    def __init__(self, order_supply):
        self.order_supply = order_supply

    def _collect_rows(self):
        orders_qs = (
            self.order_supply.orders
            .exclude(status=ContractorOrder.Status.CANCELLED)
            .select_related('contractor_user__contractor')
            .prefetch_related(
                Prefetch('order_items', queryset=ContractorOrderItem.objects.select_related('product'))
            )
            .all()
        )
        rows = []
        seen_contractors = {}
        product_prices = {}
        for order in orders_qs:
            cu = order.contractor_user
            company = getattr(cu, 'contractor', None)
            contractor_name = getattr(company, 'name', None) or str(company or cu)
            if cu.id not in seen_contractors:
                seen_contractors[cu.id] = contractor_name
            for item in order.order_items.all():
                prod = item.product
                prod_name = getattr(prod, 'name', None) or str(prod)
                product_prices[prod_name] = float(getattr(prod, 'price', 0) or 0)
                rows.append({
                    'product_name': prod_name,
                    'contractor_name': contractor_name,
                    'quantity': int(item.quantity),
                })
        contractors = [name for _, name in seen_contractors.items()]
        return rows, contractors, product_prices

    def _build_pivot_df(self, rows, product_prices):
        if not rows:
            return pd.DataFrame(columns=['', 'Цена'])
        df_raw = pd.DataFrame(rows)
        pivot = pd.pivot_table(
            df_raw,
            index='product_name',
            columns='contractor_name',
            values='quantity',
            aggfunc='sum',
            fill_value=0
        )
        df = pivot.reset_index()
        df.rename(columns={'product_name': ''}, inplace=True)
        df.insert(1, 'Цена', df[''].map(product_prices).fillna(0))
        return df

    def _create_formats(self, workbook):
        header_format = workbook.add_format({
            'font_name': self.FONT_NAME,
            'font_size': self.FONT_SIZE,
            'bold': True,
            'text_wrap': True,
            'valign': 'center',
            'align': 'center',
        })
        text_format = workbook.add_format({
            'font_name': self.FONT_NAME,
            'font_size': self.FONT_SIZE,
            'text_wrap': True,
            'valign': 'top',
        })
        number_format = workbook.add_format({
            'font_name': self.FONT_NAME,
            'font_size': self.FONT_SIZE,
            'valign': 'top',
            'num_format': '0',
        })
        total_header_format = workbook.add_format({
            'font_name': self.FONT_NAME,
            'font_size': self.FONT_SIZE,
            'bold': True,
            'text_wrap': True,
            'valign': 'center',
            'align': 'center',
            'bg_color': '#F2F2F2',
            'border': 1,
        })
        total_number_format = workbook.add_format({
            'font_name': self.FONT_NAME,
            'font_size': self.FONT_SIZE,
            'valign': 'top',
            'num_format': '0',
            'bold': True,
            'border': 1,
        })
        price_format = workbook.add_format({
            'font_name': self.FONT_NAME,
            'font_size': self.FONT_SIZE,
            'valign': 'top',
            'num_format': '0.00',
        })
        total_price_format = workbook.add_format({
            'font_name': self.FONT_NAME,
            'font_size': self.FONT_SIZE,
            'valign': 'top',
            'num_format': '0.00',
            'bold': True,
            'border': 1,
        })
        return {
            'header': header_format,
            'text': text_format,
            'number': number_format,
            'price': price_format,
            'total_header': total_header_format,
            'total_number': total_number_format,
            'total_price': total_price_format,
        }

    def _write_table_and_formats(self, worksheet, df, formats):
        nrows = len(df)
        ncols = len(df.columns)
        for col_idx, col_name in enumerate(df.columns):
            width = self.FIRST_COL_WIDTH if col_idx == 0 else self.OTHER_COL_WIDTH
            worksheet.set_column(col_idx, col_idx, width)
            worksheet.write(0, col_idx, col_name or '', formats['header'])
        for row_idx in range(1, nrows + 1):
            for col_idx in range(0, ncols):
                value = df.iloc[row_idx - 1, col_idx]
                if col_idx == 0:
                    worksheet.write(row_idx, col_idx, value, formats['text'])
                elif col_idx == 1:
                    worksheet.write(row_idx, col_idx, value, formats['price'])
                else:
                    worksheet.write(row_idx, col_idx, value, formats['number'])

    def _write_total_column(self, worksheet, df, formats):
        nrows = len(df)
        ncols = len(df.columns)
        total_col_idx = ncols
        worksheet.set_column(total_col_idx, total_col_idx, self.TOTAL_COL_WIDTH)
        worksheet.write(0, total_col_idx, 'Общее количество', formats['total_header'])
        first_data_col = 2  # skip product name (0) and price (1)
        last_data_col = ncols - 1 if ncols - 1 >= first_data_col else first_data_col
        for row_idx in range(1, nrows + 1):
            start_col_letter = xl_col_to_name(first_data_col)
            end_col_letter = xl_col_to_name(last_data_col)
            excel_row = row_idx + 0
            formula = f"=SUM({start_col_letter}{excel_row + 1}:{end_col_letter}{excel_row + 1})"
            worksheet.write_formula(row_idx, total_col_idx, formula, formats['total_number'])

    def _write_total_row(self, worksheet, df, formats):
        nrows = len(df)
        ncols = len(df.columns)
        total_row_idx = nrows + 1  # row after all data rows (0-indexed)
        worksheet.write(total_row_idx, 0, 'Итого', formats['total_header'])
        price_col_letter = xl_col_to_name(1)  # B — цена
        first_excel_data_row = 2
        last_excel_data_row = nrows + 1
        for col_idx in range(2, ncols):  # warehouse columns only
            col_letter = xl_col_to_name(col_idx)
            formula = (
                f"=SUMPRODUCT("
                f"{price_col_letter}{first_excel_data_row}:{price_col_letter}{last_excel_data_row},"
                f"{col_letter}{first_excel_data_row}:{col_letter}{last_excel_data_row})"
            )
            worksheet.write_formula(total_row_idx, col_idx, formula, formats['total_price'])

    def generate_xlsx_bytes(self):
        rows, contractors, product_prices = self._collect_rows()
        df = self._build_pivot_df(rows, product_prices)
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
            sheet_name = 'Заявка'
            df.to_excel(writer, index=False, sheet_name=sheet_name)
            workbook = writer.book
            worksheet = writer.sheets[sheet_name]
            formats = self._create_formats(workbook)
            self._write_table_and_formats(worksheet, df, formats)
            self._write_total_column(worksheet, df, formats)
            self._write_total_row(worksheet, df, formats)
            total_cols = len(df.columns) + 1
            worksheet.autofilter(0, 0, len(df), total_cols - 1)
            worksheet.freeze_panes(1, 1)
        buffer.seek(0)
        date = getattr(self.order_supply, 'date')
        date_str = date.strftime('%d.%m.%Y')
        filename = f'Заявка на {date_str}.xlsx'
        return buffer.getvalue(), filename
