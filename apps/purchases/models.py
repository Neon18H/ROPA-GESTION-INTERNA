from django.db import models
from apps.accounts.models import OrganizationScopedModel, User
from apps.inventory.models import Variant


class Supplier(OrganizationScopedModel):
    name = models.CharField(max_length=150)
    phone = models.CharField(max_length=32, blank=True)
    email = models.EmailField(blank=True)
    address = models.CharField(max_length=255, blank=True)
    notes = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['organization', 'name'], name='uq_org_supplier_name')]

    def __str__(self):
        return self.name


class PurchaseOrder(OrganizationScopedModel):
    class Status(models.TextChoices):
        DRAFT = 'DRAFT', 'Borrador'
        RECEIVED = 'RECEIVED', 'Recibida'
        CANCELLED = 'CANCELLED', 'Cancelada'

    number = models.IntegerField()
    supplier = models.ForeignKey(Supplier, on_delete=models.PROTECT)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.DRAFT)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    tax_total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    created_by = models.ForeignKey(User, null=True, on_delete=models.SET_NULL)
    notes = models.TextField(blank=True)

    def __str__(self):
        return str(self.number)


class PurchaseItem(models.Model):
    purchase = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE, related_name='items')
    variant = models.ForeignKey(Variant, on_delete=models.PROTECT)
    qty = models.IntegerField()
    unit_cost = models.DecimalField(max_digits=12, decimal_places=2)
    line_total = models.DecimalField(max_digits=12, decimal_places=2)
