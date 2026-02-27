from pathlib import Path
from uuid import uuid4

from django.db import models
from django.db.models import F
from apps.accounts.models import OrganizationScopedModel, User
from apps.common.storage import get_media_storage


def product_image_upload_to(instance, filename):
    extension = Path(filename).suffix.lower() or '.jpg'
    safe_filename = f'{uuid4().hex}{extension}'
    product_id = instance.id or 'new'
    return f'org_{instance.organization_id}/products/{product_id}/{safe_filename}'


def variant_image_upload_to(instance, filename):
    extension = Path(filename).suffix.lower() or '.jpg'
    safe_filename = f'{uuid4().hex}{extension}'
    variant_id = instance.id or 'new'
    organization_id = getattr(getattr(instance, 'product', None), 'organization_id', None) or 'unknown'
    return f'org_{organization_id}/variants/{variant_id}/{safe_filename}'


class Category(OrganizationScopedModel):
    name = models.CharField(max_length=120)

    def __str__(self):
        name = (getattr(self, 'name', '') or '').strip()
        return name or f'Category #{getattr(self, "pk", "")}'


class Brand(OrganizationScopedModel):
    name = models.CharField(max_length=120)

    def __str__(self):
        name = (getattr(self, 'name', '') or '').strip()
        return name or f'Brand #{getattr(self, "pk", "")}'


class Product(OrganizationScopedModel):
    sku = models.CharField(max_length=64)
    name = models.CharField(max_length=180)
    category = models.ForeignKey(Category, null=True, blank=True, on_delete=models.SET_NULL)
    brand = models.ForeignKey(Brand, null=True, blank=True, on_delete=models.SET_NULL)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to=product_image_upload_to, storage=get_media_storage, null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['organization', 'sku'], name='uq_org_sku')]

    def __str__(self):
        sku = (getattr(self, 'sku', '') or '').strip()
        name = (getattr(self, 'name', '') or '').strip()
        if sku and name:
            return f'{sku} - {name}'
        return sku or name or f'Product #{getattr(self, "pk", "")}'


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
    image = models.ImageField(upload_to=variant_image_upload_to, storage=get_media_storage, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    default_sale_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    cost = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)

    def __str__(self):
        product_name = ((getattr(self, 'product', None) and self.product.name) or '').strip()
        base = product_name or f'Variant #{getattr(self, "pk", "")}'

        extras = []
        size = (getattr(self, 'size', '') or '').strip()
        color = (getattr(self, 'color', '') or '').strip()
        if size:
            extras.append(size)
        if color:
            extras.append(color)
        return f"{base} - {'/'.join(extras)}" if extras else base


class Stock(models.Model):
    variant = models.OneToOneField(Variant, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=0)
    min_alert = models.IntegerField(default=3)
    last_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    avg_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)


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


    @property
    def movement_type(self):
        return self.type

    @property
    def quantity(self):
        return self.qty

    def apply_to_stock(self):
        stock, _ = Stock.objects.get_or_create(variant=self.variant)
        if self.type == self.Type.IN:
            stock.quantity = F('quantity') + self.qty
        elif self.type == self.Type.OUT:
            stock.quantity = F('quantity') - self.qty
        else:
            stock.quantity = F('quantity') + self.qty
        stock.save(update_fields=['quantity'])
