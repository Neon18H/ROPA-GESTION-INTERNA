from decimal import Decimal

from django.db import models

from apps.accounts.models import Organization
from apps.common.crypto import decrypt_secret, encrypt_secret


class StoreSettings(models.Model):
    class Currency(models.TextChoices):
        COP = 'COP', 'COP'
        USD = 'USD', 'USD'

    class RoundingPolicy(models.TextChoices):
        BANKERS = 'BANKERS', 'Bankers'
        HALF_UP = 'HALF_UP', 'Half up'

    organization_id = models.BigIntegerField(unique=True, db_index=True)
    currency = models.CharField(max_length=8, default='COP')
    base_currency = models.CharField(max_length=3, choices=Currency.choices, default=Currency.COP)
    fx_usd_cop_rate = models.DecimalField(max_digits=18, decimal_places=6, default=Decimal('0'))
    show_dual_currency = models.BooleanField(default=True)
    rounding_policy = models.CharField(max_length=16, choices=RoundingPolicy.choices, default=RoundingPolicy.HALF_UP)
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

    def get_org(self):
        return Organization.objects.using('default').get(id=self.organization_id)


class EmailSettings(models.Model):
    organization_id = models.BigIntegerField(unique=True, db_index=True)
    smtp_host = models.CharField(max_length=160, blank=True, default='')
    smtp_port = models.PositiveIntegerField(default=587)
    smtp_username = models.CharField(max_length=160, blank=True, default='')
    smtp_password_ciphertext = models.TextField(blank=True, default='')
    smtp_password_nonce = models.CharField(max_length=64, blank=True, default='')
    smtp_password_kid = models.CharField(max_length=32, blank=True, default='')
    smtp_use_tls = models.BooleanField(default=True)
    smtp_from_email = models.EmailField(blank=True, default='')
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'EmailSettings({self.organization_id})'

    def get_org(self):
        return Organization.objects.using('default').get(id=self.organization_id)

    @property
    def smtp_password(self):
        return decrypt_secret(self.smtp_password_ciphertext, self.smtp_password_nonce)

    def set_smtp_password(self, plaintext):
        encrypted = encrypt_secret(plaintext)
        self.smtp_password_ciphertext = encrypted['ciphertext']
        self.smtp_password_nonce = encrypted['nonce']
        self.smtp_password_kid = encrypted['kid']
