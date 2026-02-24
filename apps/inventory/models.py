from django.db import models
from django.db.models import F
from apps.accounts.models import OrganizationScopedModel, User


class Category(OrganizationScopedModel):
    name = models.CharField(max_length=120)


class Brand(OrganizationScopedModel):
    name = models.CharField(max_length=120)


class Product(OrganizationScopedModel):
    sku = models.CharField(max_length=64)
    name = models.CharField(max_length=180)
    category = models.ForeignKey(Category, null=True, blank=True, on_delete=models.SET_NULL)
    brand = models.ForeignKey(Brand, null=True, blank=True, on_delete=models.SET_NULL)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['organization', 'sku'], name='uq_org_sku')]


class Variant(models.Model):
    class Gender(models.TextChoices):
        HOMBRE = 'HOMBRE', 'Hombre'
        MUJER = 'MUJER', 'Mujer'
        UNISEX = 'UNISEX', 'Unisex'

    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    size = models.CharField(max_length=16)
    color = models.CharField(max_length=32)
    gender = models.CharField(max_length=12, choices=Gender.choices, default=Gender.UNISEX)
    barcode = models.CharField(max_length=64, blank=True)
    is_active = models.BooleanField(default=True)


class Stock(models.Model):
    variant = models.OneToOneField(Variant, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=0)
    min_alert = models.IntegerField(default=3)


class KardexEntry(OrganizationScopedModel):
    class Type(models.TextChoices):
        IN = 'IN', 'Entrada'
        OUT = 'OUT', 'Salida'
        ADJUST = 'ADJUST', 'Ajuste'

    variant = models.ForeignKey(Variant, on_delete=models.PROTECT)
    type = models.CharField(max_length=10, choices=Type.choices)
    qty = models.IntegerField()
    unit_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    note = models.CharField(max_length=255, blank=True)
    reference = models.CharField(max_length=80, blank=True)
    created_by = models.ForeignKey(User, null=True, on_delete=models.SET_NULL)

    def apply_to_stock(self):
        stock, _ = Stock.objects.get_or_create(variant=self.variant)
        if self.type == self.Type.IN:
            stock.quantity = F('quantity') + self.qty
        elif self.type == self.Type.OUT:
            stock.quantity = F('quantity') - self.qty
        else:
            stock.quantity = F('quantity') + self.qty
        stock.save(update_fields=['quantity'])
