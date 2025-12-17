from django.db import models
from django.core.validators import RegexValidator, MinValueValidator, MaxValueValidator
from simple_history.models import HistoricalRecords


class BaseInfo(models.Model):
    name = models.CharField(
        "Название",
        max_length=512,
    )
    address = models.TextField(
        "Адрес",
        max_length=512,
        null=True,
        blank=True,
        help_text="Для этикеток товаров",
    )
    short_address = models.TextField(
        "Короткий адрес",
        max_length=512,
        null=True,
        blank=True,
        help_text="Для этикеток контрагентов",
    )
    phone_number = models.CharField(
        "Номер телефона",
        max_length=32,
        null=True,
        blank=True,
    )
    site_url = models.URLField(
        "Адрес сайта",
        max_length=512,
        null=True,
        blank=True,
        help_text="вместе с http:// или https://",
    )
    history = HistoricalRecords()

    class Meta:
        verbose_name = "общая информация"
        verbose_name_plural = "общая информация"

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.pk and BaseInfo.objects.exists():
            raise ValidationError("Можно создать только один экземпляр")
        super().save(*args, **kwargs)

    @classmethod
    def get_solo(cls):
        obj, created = cls.objects.get_or_create(pk=1)
        return obj


class Template(models.Model):
    name = models.CharField(
        "Название",
        max_length=512,
        unique=True,
    )
    width = models.FloatField(
        "Ширина",
        validators=[
            MinValueValidator(1)
        ],
    )
    height = models.FloatField(
        "Высота",
        validators=[
            MinValueValidator(1)
        ],
    )
    elements = models.JSONField("Разметка")
    history = HistoricalRecords()

    class Meta:
        verbose_name = "шаблон"
        verbose_name_plural = "шаблоны"

    def __str__(self):
        return self.name


class OrgStandart(models.Model):
    name = models.CharField(
        "Название",
        max_length=256,
        help_text="Пример: Обеденные блюда готовые, охлажденные из мяса птицы с гарнирами и без",
    )
    code = models.CharField(
        "Код",
        max_length=64,
        help_text="Пример: 71743495-001-2024",
    )
    history = HistoricalRecords()

    class Meta:
        verbose_name = "стандарт организации (СТО)"
        verbose_name_plural = "стандарты организации (СТО)"

    def __str__(self):
        return f"{self.name} СТО {self.code}"


class ContractorCategory(models.Model):
    name = models.CharField(
        "Название",
        max_length=128,
    )
    history = HistoricalRecords()

    class Meta:
        verbose_name = "контрагент"
        verbose_name_plural = "контрагенты"

    def __str__(self):
        return self.name


class Contractor(models.Model):
    category = models.ForeignKey(
        ContractorCategory,
        on_delete=models.PROTECT,
        related_name="contractor",
        verbose_name="Контрагент",
        help_text="Пример: Самокат",
    )
    name = models.CharField(
        "Название",
        max_length=128,
        null=True,
        blank=True,
        help_text="Пример: ООО «Рога и Копыта»",
    )
    city = models.CharField(
        "Город",
        max_length=128,
        default="Тюмень",
    )
    street = models.TextField(
        "Улица",
        max_length=256,
    )
    comment = models.CharField(
        "Комментарий",
        max_length=128,
        null=True,
        blank=True,
        help_text="Пример: Взрослая травматология",
    )
    history = HistoricalRecords()

    class Meta:
        verbose_name = "этикетка контрагента"
        verbose_name_plural = "этикетки контрагентов"
        ordering = ["-category__name", "city", "street", "name",]

    @property
    def entity_template(self):
        return self.contractor_template.first()

    def __str__(self):
        name = self.category.name
        if self.name:
            name += f": {self.name}"
        return f"{name}, {self.street}"


class ContractorTemplate(models.Model):
    contractor = models.ForeignKey(
        Contractor,
        on_delete=models.CASCADE,
        related_name="contractor_template",
        verbose_name="Контрагент",
    )
    template = models.ForeignKey(
        Template,
        on_delete=models.PROTECT,
        related_name="contractor_template",
        verbose_name="Шаблон",
    )

    class Meta:
        verbose_name = "этикетка контрагента (template)"
        verbose_name_plural = "этикетки контрагентов (template)"

    def __str__(self):
        return f"{self.contractor.category.name} {self.contractor.name if self.contractor.name else ''} ({self.template.name})"


class ProductCategory(models.Model):
    name = models.CharField(
        "Название",
        max_length=128,
    )

    class Meta:
        verbose_name = "категория товара"
        verbose_name_plural = "категории товаров"

    def __str__(self):
        return self.name


class Product(models.Model):
    category = models.ForeignKey(
        ProductCategory,
        on_delete=models.PROTECT,
        related_name="product",
        verbose_name="Категория",
    )
    name = models.TextField(
        "Название",
        max_length=82,
    )
    ingredients = models.TextField(
        "Состав",
        max_length=1600,
    )
    weight = models.CharField(
        "Вес",
        max_length=100,
        help_text="Пример: 100/130 гр.",
    )
    best_before = models.PositiveIntegerField(
        "Срок хранения",
        default=4,
        help_text="Количество дней",
    )
    calories = models.DecimalField(
        "Калории",
        max_digits=6,
        decimal_places=2,
    )
    protein = models.DecimalField(
        "Белки",
        max_digits=6,
        decimal_places=2,
    )
    fat = models.DecimalField(
        "Жиры",
        max_digits=6,
        decimal_places=2,
    )
    carbs = models.DecimalField(
        "Углеводы",
        max_digits=6,
        decimal_places=2,
    )
    barcode = models.CharField(
        "Штрихкод",
        max_length=13,
        validators=[
            RegexValidator(regex=r'^\d{13}$',message='Штрихкод должен содержать ровно 13 цифр'),
        ]
    )
    caption = models.TextField(
        "Дополнительная информация",
        default="Хранить при температуре от 0 до +6°С. Продукция может содержать аллергены: сельдерей, соя, арахис, орехи, рыба, морепродукты, пшеница.",
    )
    history = HistoricalRecords()

    class Meta:
        verbose_name = "этикетка товара"
        verbose_name_plural = "этикетки товаров"
        ordering = ["-category__name", "name",]

    @property
    def entity_template(self):
        return self.product_template.first()

    def __str__(self):
        return self.name


class ProductTemplate(models.Model):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="product_template",
        verbose_name="Товар",
    )
    template = models.ForeignKey(
        Template,
        on_delete=models.PROTECT,
        related_name="product_template",
        verbose_name="Шаблон",
    )

    class Meta:
        verbose_name = "этикетка товара (template)"
        verbose_name_plural = "этикетки товаров (template)"

    def __str__(self):
        return f"{self.product.name} ({self.template.name})"


class ProductOrgStandart(models.Model):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="org_standart",
        verbose_name="Товар",
    )
    org_standart = models.ForeignKey(
        OrgStandart,
        on_delete=models.PROTECT,
        related_name="org_standart",
        verbose_name="Стандарт Организации (СТО)",
    )

    class Meta:
        verbose_name = "стандарт организации (СТО)"
        verbose_name_plural = "стандарты организации (СТО)"

    def __str__(self):
        return f"{self.product.name} ({self.org_standart.name} СТО {self.org_standart.code})"
