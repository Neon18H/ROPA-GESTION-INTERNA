from django.db import transaction

from apps.inventory.models import KardexEntry


@transaction.atomic
def process_return(return_order, user):
    for item in return_order.items.select_related('variant').all():
        if item.action == item.Action.RESTOCK:
            movement_type = KardexEntry.Type.IN
            qty = item.qty
        else:
            movement_type = KardexEntry.Type.ADJUST
            qty = -item.qty

        kardex = KardexEntry.objects.create(
            organization=return_order.organization,
            variant=item.variant,
            type=movement_type,
            qty=qty,
            reference=f'return:{return_order.id}',
            note=return_order.reason,
            created_by=user,
        )
        kardex.apply_to_stock()
