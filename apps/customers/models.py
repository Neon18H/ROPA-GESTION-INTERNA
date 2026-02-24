from django.db import models
from apps.accounts.models import OrganizationScopedModel


class Customer(OrganizationScopedModel):
    class Type(models.TextChoices):
        NORMAL = 'NORMAL', 'Normal'
        MAYORISTA = 'MAYORISTA', 'Mayorista'

    name = models.CharField(max_length=150)
    phone = models.CharField(max_length=32, blank=True)
    email = models.EmailField(blank=True)
    document_id = models.CharField(max_length=40, blank=True)
    type = models.CharField(max_length=15, choices=Type.choices, default=Type.NORMAL)
    notes = models.TextField(blank=True)


class Loyalty(models.Model):
    customer = models.OneToOneField(Customer, on_delete=models.CASCADE)
    points = models.IntegerField(default=0)
    tier = models.CharField(max_length=20, default='Base')


class CreditAccount(models.Model):
    customer = models.OneToOneField(Customer, on_delete=models.CASCADE)
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    limit = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    due_date = models.DateField(null=True, blank=True)
