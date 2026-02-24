from django.db import models
from apps.accounts.models import OrganizationScopedModel


class Promotion(OrganizationScopedModel):
    class Type(models.TextChoices):
        PERCENT = 'PERCENT', 'Porcentaje'
        FIXED = 'FIXED', 'Fijo'
        BOGO = 'BOGO', '2x1'
        SECOND_HALF = 'SECOND_HALF', 'Segundo al 50'

    name = models.CharField(max_length=120)
    type = models.CharField(max_length=20, choices=Type.choices)
    value = models.DecimalField(max_digits=10, decimal_places=2)
    start_date = models.DateField()
    end_date = models.DateField()
    is_active = models.BooleanField(default=True)


class PromotionRule(models.Model):
    class AppliesTo(models.TextChoices):
        CATEGORY = 'CATEGORY', 'Categoría'
        PRODUCT = 'PRODUCT', 'Producto'
        VARIANT = 'VARIANT', 'Variante'

    promotion = models.ForeignKey(Promotion, on_delete=models.CASCADE, related_name='rules')
    applies_to = models.CharField(max_length=12, choices=AppliesTo.choices)
    target_id = models.PositiveIntegerField()
    conditions = models.JSONField(default=dict, blank=True)
