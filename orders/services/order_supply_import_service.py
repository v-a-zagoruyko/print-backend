import io
from dataclasses import dataclass
from typing import List, Set, Tuple

import pandas as pd
from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone

from main.models import Contractor, ContractorCategory, Product
from orders.models import ContractorOrder, ContractorOrderItem, ContractorUser, OrderSupply


class OrderSupplyImportError(Exception):
    pass


@dataclass
class OrderSupplyImportResult:
    order_supply: OrderSupply
    created_orders: int
    updated_orders: int
    created_items: int
    updated_items: int
    missing_barcodes: List[str]


class OrderSupplyImportService:
    DATE_COL_NAME = "Дата поступления заказа"
    WAREHOUSE_COL_NAME = "Название склада"
    BARCODE_COL_NAME = "Штрихкод"
    QUANTITY_COL_NAME = "Количество"

    # zero-based fallback indices (C, F, H, L)
    DATE_COL_INDEX = 3
    WAREHOUSE_COL_INDEX = 5
    BARCODE_COL_INDEX = 7
    QUANTITY_COL_INDEX = 11

    def __init__(self, uploaded_file, user):
        self.uploaded_file = uploaded_file
        self.user = user

    def _get_or_create_default_category(self) -> ContractorCategory:
        return ContractorCategory.objects.get_or_create(name="Импорт поставщика")[0]

    def _resolve_column(self, df: pd.DataFrame, name: str, index: int) -> pd.Series:
        if name in df.columns:
            return df[name]
        try:
            return df.iloc[:, index]
        except IndexError as exc:
            raise OrderSupplyImportError(
                f"В файле отсутствует ожидаемый столбец «{name}» (и fallback по индексу)."
            ) from exc

    def _extract_date(self, date_series: pd.Series):
        dates = date_series.dropna().unique()
        if len(dates) == 0:
            raise OrderSupplyImportError("Не удалось определить дату заказа из файла.")
        if len(dates) > 1:
            raise OrderSupplyImportError("В файле указано несколько разных дат заказа.")

        date_value = pd.to_datetime(dates[0]).date()
        today = timezone.localdate()
        if date_value < today:
            raise OrderSupplyImportError(
                f"Дата заказа {date_value.strftime('%d.%m.%Y')} не может быть в прошлом."
            )
        return date_value

    @transaction.atomic
    def import_data(self) -> OrderSupplyImportResult:
        try:
            df = pd.read_excel(self.uploaded_file)
        except Exception as exc:  # pragma: no cover - defensive
            raise OrderSupplyImportError("Не удалось прочитать Excel-файл.") from exc

        if df.empty:
            raise OrderSupplyImportError("Файл пустой.")

        date_series = self._resolve_column(df, self.DATE_COL_NAME, self.DATE_COL_INDEX)
        warehouse_series = self._resolve_column(
            df, self.WAREHOUSE_COL_NAME, self.WAREHOUSE_COL_INDEX
        )
        barcode_series = self._resolve_column(
            df, self.BARCODE_COL_NAME, self.BARCODE_COL_INDEX
        )
        quantity_series = self._resolve_column(
            df, self.QUANTITY_COL_NAME, self.QUANTITY_COL_INDEX
        )

        date_value = self._extract_date(date_series)

        order_supply, _ = OrderSupply.objects.get_or_create(date=date_value)

        default_category = self._get_or_create_default_category()

        created_orders = 0
        updated_orders = 0
        created_items = 0
        updated_items = 0
        missing_barcodes: Set[str] = set()

        orders_for_supply: Set[ContractorOrder] = set()

        data = pd.DataFrame(
            {
                "date": date_series,
                "warehouse": warehouse_series,
                "barcode": barcode_series,
                "quantity": quantity_series,
            }
        ).dropna(subset=["warehouse", "barcode", "quantity"])

        if data.empty:
            raise OrderSupplyImportError(
                "После фильтрации пустых строк не осталось ни одной записи для импорта."
            )

        for (_, row) in data.iterrows():
            warehouse_name = str(row["warehouse"]).strip()
            barcode = str(row["barcode"]).strip()

            try:
                quantity = int(row["quantity"])
            except (TypeError, ValueError):
                continue

            if quantity <= 0:
                continue

            contractor, _ = Contractor.objects.get_or_create(
                name=warehouse_name,
                defaults={
                    "category": default_category,
                    "city": "Тюмень",
                    "street": warehouse_name,
                },
            )

            contractor_user, _ = ContractorUser.objects.get_or_create(
                contractor=contractor,
                user=self.user,
                defaults={"status": ContractorUser.Status.ACTIVE},
            )

            contractor_order, created = ContractorOrder.objects.get_or_create(
                contractor_user=contractor_user,
                date=date_value,
                defaults={"status": ContractorOrder.Status.CREATED},
            )
            if created:
                created_orders += 1
            else:
                updated_orders += 1

            orders_for_supply.add(contractor_order)

            try:
                product = Product.objects.get(barcode=barcode)
            except Product.DoesNotExist:
                missing_barcodes.add(barcode)
                continue

            item, created_item = ContractorOrderItem.objects.update_or_create(
                order=contractor_order,
                product=product,
                defaults={"quantity": quantity},
            )
            if created_item:
                created_items += 1
            else:
                updated_items += 1

        if not orders_for_supply:
            raise OrderSupplyImportError(
                "Не удалось создать ни одной заявки контрагента. "
                "Проверьте содержимое файла."
            )

        order_supply.orders.add(*orders_for_supply)

        return OrderSupplyImportResult(
            order_supply=order_supply,
            created_orders=created_orders,
            updated_orders=updated_orders,
            created_items=created_items,
            updated_items=updated_items,
            missing_barcodes=sorted(missing_barcodes),
        )

