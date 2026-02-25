from decimal import Decimal

from django.db import models

from apps.accounts.models import Organization


class StoreSettings(models.Model):
    organization = models.OneToOneField(Organization, on_delete=models.CASCADE)
    currency = models.CharField(max_length=8, default='COP')
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=19)
    invoice_prefix = models.CharField(max_length=10, default='FAC')
    next_invoice_number = models.IntegerField(default=1)
    low_stock_default = models.IntegerField(default=3)
    sizes = models.JSONField(default=list, blank=True)
    colors = models.JSONField(default=list, blank=True)
    categories_custom = models.JSONField(default=list, blank=True)

    billing_legal_name = models.CharField(max_length=160, blank=True, default='')
    billing_tax_id = models.CharField(max_length=40, blank=True, default='')
    billing_address = models.CharField(max_length=200, blank=True, default='')
    billing_postal_code = models.CharField(max_length=20, blank=True, default='')
    billing_email = models.EmailField(blank=True, default='')
    billing_phone = models.CharField(max_length=32, blank=True, default='')
    billing_city = models.CharField(max_length=80, blank=True, default='')
    billing_country = models.CharField(max_length=80, blank=True, default='')
    billing_vat_rate = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'))

    def __str__(self):
        return f'StoreSettings({self.organization_id})'
