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
