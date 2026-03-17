from django.db import models
from django.core.validators import RegexValidator, MinValueValidator, MaxValueValidator
from simple_history.models import HistoricalRecords


# TODO: Move to labels app
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


# TODO: Move to labels app
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


# TODO: Move to labels app
class ContractorCategory(models.Model):
    name = models.CharField(
        "Название",
        max_length=128,
    )
    history = HistoricalRecords()

    class Meta:
        verbose_name = "фирма-контрагент"
        verbose_name_plural = "фирмы-контрагенты"

    def __str__(self):
        return self.name


# TODO: Move to labels app
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
        return f"{name}, г. {self.city}, ул. {self.street}"


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


class Workshop(models.Model):
    name = models.CharField(
        "Название",
        max_length=128,
    )

    class Meta:
        verbose_name = "цех"
        verbose_name_plural = "цеха"
        ordering = ["name"]

    def __str__(self):
        return self.name


class ProductCategory(models.Model):
    name = models.CharField(
        "Название",
        max_length=128,
    )
    workshop = models.ForeignKey(
        Workshop,
        on_delete=models.PROTECT,
        related_name="product_categories",
        verbose_name="Цех",
        null=True,
        blank=True,
    )

    class Meta:
        verbose_name = "категория товара"
        verbose_name_plural = "категории товаров"

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    name = models.CharField(
        "Название",
        max_length=128,
        unique=True,
    )

    class Meta:
        verbose_name = "ингредиент"
        verbose_name_plural = "ингредиенты"
        ordering = ["name"]

    def __str__(self):
        return self.name


# TODO: Move to labels app
class Product(models.Model):
    class ProductStatus(models.TextChoices):
        AVAILABLE = "CREATED", "Доступен"
        ARCHIEVED = "ARCHIEVED", "Архивирован"

    status = models.CharField(
        "Статус",
        max_length=150,
        choices=ProductStatus.choices,
        default=ProductStatus.AVAILABLE
    )
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
        null=True,
        blank=True,
    )
    weight = models.CharField(
        "Вес",
        max_length=100,
        help_text="Пример: 100/130 гр.",
    )
    calories = models.DecimalField(
        "Калории",
        max_digits=6,
        decimal_places=2,
        help_text="На 100 г. продукта",
    )
    protein = models.DecimalField(
        "Белки",
        max_digits=6,
        decimal_places=2,
        help_text="На 100 г. продукта",
    )
    fat = models.DecimalField(
        "Жиры",
        max_digits=6,
        decimal_places=2,
        help_text="На 100 г. продукта",
    )
    carbs = models.DecimalField(
        "Углеводы",
        max_digits=6,
        decimal_places=2,
        help_text="На 100 г. продукта",
    )
    barcode = models.CharField(
        "Штрихкод",
        max_length=13,
        validators=[
            RegexValidator(
                regex=r'^(\d{13})?$',
                message='Штрихкод должен быть пустым или содержать ровно 13 цифр',
            ),
        ],
        null=True,
        blank=True,
    )
    caption = models.TextField(
        "Дополнительная информация",
        default="Хранить при температуре от 0 до +6°С. Продукция может содержать аллергены: сельдерей, соя, арахис, орехи, рыба, морепродукты, пшеница.",
        null=True,
        blank=True,
    )
    quantity = models.PositiveIntegerField(
        "Количество",
        null=True,
        blank=True,
    )
    ingredients_m2m = models.ManyToManyField(
        Ingredient,
        through="ProductIngredient",
        related_name="products",
        verbose_name="Ингредиенты",
        blank=True,
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


class ProductIngredient(models.Model):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="product_ingredients",
        verbose_name="Товар",
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.PROTECT,
        related_name="product_ingredients",
        verbose_name="Ингредиент",
    )
    weight_grams = models.PositiveIntegerField(
        "Вес, г",
    )

    class Meta:
        verbose_name = "ингредиент товара"
        verbose_name_plural = "ингредиенты товаров"
        constraints = [
            models.UniqueConstraint(
                fields=["product", "ingredient"],
                name="uniq_product_ingredient",
            )
        ]

    def __str__(self):
        return f"{self.product.name}: {self.ingredient.name} ({self.weight_grams} г)"


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
