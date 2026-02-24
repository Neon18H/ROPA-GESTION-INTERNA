from django.db import models
from apps.accounts.models import OrganizationScopedModel, User
from apps.customers.models import Customer
from apps.inventory.models import Variant, KardexEntry


class Sale(OrganizationScopedModel):
    class PaymentMethod(models.TextChoices):
        CASH = 'CASH', 'Efectivo'
        CARD = 'CARD', 'Tarjeta'
        TRANSFER = 'TRANSFER', 'Transferencia'

    class Status(models.TextChoices):
        PAID = 'PAID', 'Pagada'
        VOID = 'VOID', 'Anulada'

    number = models.IntegerField()
    customer = models.ForeignKey(Customer, null=True, blank=True, on_delete=models.SET_NULL)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    discount_total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    tax_total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    payment_method = models.CharField(max_length=16, choices=PaymentMethod.choices, default=PaymentMethod.CASH)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PAID)
    created_by = models.ForeignKey(User, null=True, on_delete=models.SET_NULL)


class SaleItem(models.Model):
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE, related_name='items')
    variant = models.ForeignKey(Variant, on_delete=models.PROTECT)
    qty = models.IntegerField()
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    discount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    line_total = models.DecimalField(max_digits=12, decimal_places=2)


class Payment(models.Model):
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE)
    method = models.CharField(max_length=16)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    reference = models.CharField(max_length=120, blank=True)


def generate_sale_kardex(sale):
    for item in sale.items.select_related('variant__product'):
        KardexEntry.objects.create(
            organization=sale.organization,
            variant=item.variant,
            type=KardexEntry.Type.OUT if sale.status == Sale.Status.PAID else KardexEntry.Type.IN,
            qty=item.qty,
            unit_cost=0,
            reference=f'sale:{sale.id}',
            created_by=sale.created_by,
        )
