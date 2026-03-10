from django.conf import settings
from django.db import models
from django.db.models import Q
from django.db.models.functions import Now
from django.db.models.functions import TruncDate
from django.utils import timezone
from simple_history.models import HistoricalRecords
from main.models import Product, Contractor


class ContractorUser(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Активен"
        INACTIVE = "INACTIVE", "Не активен"

    status = models.CharField(
        "Статус",
        max_length=30,
        choices=Status.choices,
        default=Status.ACTIVE,
    )
    contractor = models.ForeignKey(
        Contractor,
        on_delete=models.CASCADE,
        related_name="contractor_user",
        verbose_name="Контрагент",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="contractor_user",
        verbose_name="Пользователь",
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["contractor"],
                condition=Q(status="ACTIVE"),
                name="unique_active_contractor_user",
            )
        ]
        verbose_name = "пользователь"
        verbose_name_plural = "пользователи"

    def __str__(self):
        return f"{self.contractor.name if self.contractor.name else self.contractor.category.name} г. {self.contractor.city}, ул. {self.contractor.street}"


class ContractorOrder(models.Model):
    class Status(models.TextChoices):
        CREATED = "CREATED", "Создан"
        PROCESSED = "PROCESSED", "Исполнен"
        CANCELLED = "CANCELLED", "Отменен"

    date = models.DateField(
        "Дата",
        default=timezone.localdate,
    )
    status = models.CharField(
        "Статус",
        max_length=30,
        choices=Status.choices,
        default=Status.CREATED,
    )
    contractor_user = models.ForeignKey(
        ContractorUser,
        on_delete=models.PROTECT,
        related_name="contractor_orders",
        verbose_name="Контрагент",
    )
    created_at = models.DateTimeField(
        "Создано",
        auto_now_add=True,
    )
    updated_at = models.DateTimeField(
        "Обновлено",
        auto_now=True,
    )
    history = HistoricalRecords()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["contractor_user", "date"],
                name="unique_contractor_date"
            ),
            models.CheckConstraint(
                check=Q(date__gte=TruncDate(Now())),
                name='date_not_in_past'
            )
        ]
        indexes = [
            models.Index(fields=["created_at"]),
            models.Index(fields=["status"]),
        ]
        ordering = ["-date", "-created_at", "-updated_at",]
        verbose_name = "заявка (пользователь)"
        verbose_name_plural = "заявки (пользователь)"

    def __str__(self):
        return f"{self.created_at.strftime('%d.%m.%y')} - {self.contractor_user}"


class ContractorOrderItem(models.Model):
    order = models.ForeignKey(
        ContractorOrder,
        on_delete=models.CASCADE,
        verbose_name="Заявка",
        related_name="order_items",
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        verbose_name="Товар",
    )
    quantity = models.PositiveIntegerField(
        "Количество",
        default=1,
    )
    history = HistoricalRecords()

    class Meta:
        unique_together = ("order", "product")
        verbose_name = "товар из заявки"
        verbose_name_plural = "товары из заявки"

    def __str__(self):
        return f"{self.product.name} x {self.quantity}"


class OrderSupply(models.Model):
    orders = models.ManyToManyField(
        ContractorOrder,
        blank=True,
        verbose_name="Заявки",
        related_name="order_supplies",
    )
    date = models.DateField(
        "Дата поставки",
    )
    created_at = models.DateTimeField(
        "Создано",
        auto_now_add=True,
    )
    updated_at = models.DateTimeField(
        "Обновлено",
        auto_now=True,
    )
    history = HistoricalRecords()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["date"],
                name="unique_date"
            ),
            models.CheckConstraint(
                check=Q(date__gte=TruncDate(Now())),
                name='order_date_not_in_past'
            )
        ]
        verbose_name = "заявка (общая)"
        verbose_name_plural = "заявки (общие)"
        ordering = ["-date", "-created_at", "-updated_at",]

    def __str__(self):
        return f"Заявка от {self.created_at.strftime('%d.%m.%y')}"
