from decimal import Decimal

from django.db import transaction

from apps.inventory.models import KardexEntry, Stock


@transaction.atomic
def receive_purchase(purchase, user):
    if purchase.status == purchase.Status.RECEIVED:
        return False

    for item in purchase.items.select_related('variant').all():
        stock, _ = Stock.objects.select_for_update().get_or_create(variant=item.variant)
        old_qty = stock.quantity or 0
        old_avg = stock.avg_cost or Decimal('0.00')
        incoming_qty = item.qty or 0
        incoming_cost = item.unit_cost or Decimal('0.00')
        new_qty = old_qty + incoming_qty

        stock.quantity = new_qty
        stock.last_cost = incoming_cost
        if new_qty > 0:
            stock.avg_cost = ((old_avg * old_qty) + (incoming_cost * incoming_qty)) / new_qty
        else:
            stock.avg_cost = incoming_cost
        stock.save(update_fields=['quantity', 'last_cost', 'avg_cost'])

        KardexEntry.objects.create(
            organization=purchase.organization,
            variant=item.variant,
            type=KardexEntry.Type.IN,
            qty=incoming_qty,
            unit_cost=incoming_cost,
            note='PURCHASE',
            reference=f'purchase:{purchase.id}',
            created_by=user,
        )

    purchase.status = purchase.Status.RECEIVED
    purchase.save(update_fields=['status'])
    return True
