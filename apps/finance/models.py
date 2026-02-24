from django.db import models
from apps.accounts.models import OrganizationScopedModel, User


class Expense(OrganizationScopedModel):
    category = models.CharField(max_length=80)
    description = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    date = models.DateField()
    created_by = models.ForeignKey(User, null=True, on_delete=models.SET_NULL)


class IncomeExtra(OrganizationScopedModel):
    description = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    date = models.DateField()
