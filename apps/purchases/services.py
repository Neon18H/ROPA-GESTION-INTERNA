from decimal import Decimal

from django.db import transaction

from apps.inventory.models import KardexEntry, Stock


@transaction.atomic
def receive_purchase(purchase, user):
    for item in purchase.items.select_related('variant').all():
        kardex = KardexEntry.objects.create(
            organization=purchase.organization,
            variant=item.variant,
            type=KardexEntry.Type.IN,
            qty=item.qty,
            unit_cost=item.unit_cost,
            reference=f'purchase:{purchase.id}',
            created_by=user,
        )
        kardex.apply_to_stock()
        stock, _ = Stock.objects.get_or_create(variant=item.variant)
        previous_qty = max((stock.quantity or 0) - item.qty, 0)
        previous_avg = stock.avg_cost or Decimal('0')
        incoming_cost = item.unit_cost or Decimal('0')
        denominator = previous_qty + item.qty
        stock.last_cost = incoming_cost
        stock.avg_cost = ((previous_avg * previous_qty) + (incoming_cost * item.qty)) / denominator if denominator else incoming_cost
        stock.save(update_fields=['last_cost', 'avg_cost'])

    purchase.status = purchase.Status.RECEIVED
    purchase.save(update_fields=['status'])
