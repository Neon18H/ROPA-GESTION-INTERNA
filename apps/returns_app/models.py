from django.db import models
from apps.accounts.models import OrganizationScopedModel, User
from apps.sales.models import Sale
from apps.inventory.models import Variant


class Return(OrganizationScopedModel):
    class Type(models.TextChoices):
        REFUND = 'REFUND', 'Reembolso'
        EXCHANGE = 'EXCHANGE', 'Cambio'

    sale = models.ForeignKey(Sale, on_delete=models.PROTECT)
    type = models.CharField(max_length=12, choices=Type.choices)
    reason = models.CharField(max_length=255)
    created_by = models.ForeignKey(User, null=True, on_delete=models.SET_NULL)


class ReturnItem(models.Model):
    class Action(models.TextChoices):
        RESTOCK = 'RESTOCK', 'Reingresar'
        DAMAGED = 'DAMAGED', 'Dañado'

    return_order = models.ForeignKey(Return, on_delete=models.CASCADE, related_name='items')
    variant = models.ForeignKey(Variant, on_delete=models.PROTECT)
    qty = models.IntegerField()
    action = models.CharField(max_length=10, choices=Action.choices)
