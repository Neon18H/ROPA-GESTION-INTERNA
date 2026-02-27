from django.core.exceptions import ValidationError
from django.db import transaction

from apps.inventory.models import KardexEntry, Stock


def apply_sale_stock_out(sale, user, org):
    with transaction.atomic():
        for item in sale.items.select_related('variant'):
            try:
                stock = Stock.objects.select_for_update().get(variant=item.variant)
            except Stock.DoesNotExist as exc:
                raise ValidationError(f'Stock no configurado para la variante #{item.variant_id}.') from exc

            if stock.quantity < item.qty:
                raise ValidationError(f'Stock insuficiente para la variante #{item.variant_id}.')

            stock.quantity -= item.qty
            stock.save(update_fields=['quantity'])

            KardexEntry.objects.create(
                organization=org,
                variant=item.variant,
                type=KardexEntry.Type.OUT,
                qty=item.qty,
                unit_cost=stock.avg_cost or stock.last_cost or item.unit_price,
                reference=f'SALE:{sale.id}',
                note='Venta POS',
                created_by=user,
            )
