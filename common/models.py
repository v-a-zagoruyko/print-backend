from main.models import (
    BaseInfo,
    ContractorCategory,
    Contractor,
    OrgStandart,
    ProductOrgStandart,
    ProductCategory,
    Product,
)


class BaseInfoProxy(BaseInfo):
    class Meta:
        proxy = True
        verbose_name = "общая информация"
        verbose_name_plural = "общая информация"


class ContractorCategoryProxy(ContractorCategory):
    class Meta:
        proxy = True
        verbose_name = "контрагент (сервис)"
        verbose_name_plural = "контрагенты (сервис)"


class ContractorProxy(Contractor):
    class Meta:
        proxy = True
        verbose_name = "контрагент"
        verbose_name_plural = "контрагенты"
        ordering = ["-category__name", "city", "street", "name",]


class OrgStandartProxy(OrgStandart):
    class Meta:
        proxy = True
        verbose_name = "товар (СТО)"
        verbose_name_plural = "товары (СТО)"


class ProductOrgStandartProxy(ProductOrgStandart):
    class Meta:
        proxy = True
        verbose_name = "стандарт организации (СТО)"
        verbose_name_plural = "стандарты организации (СТО)"


class ProductCategoryProxy(ProductCategory):
    class Meta:
        proxy = True
        verbose_name = "товар (категория)"
        verbose_name_plural = "товары (категория)"


class ProductProxy(Product):
    class Meta:
        proxy = True
        verbose_name = "товар"
        verbose_name_plural = "товары"
        ordering = ["-category__name", "name",]
