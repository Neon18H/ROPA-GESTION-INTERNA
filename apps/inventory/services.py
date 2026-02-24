from decimal import Decimal

from django.db import transaction

from .models import KardexEntry


@transaction.atomic
def create_kardex_movement(*, organization, user, variant, movement_type, qty, unit_cost=Decimal('0'), note='', reference=''):
    entry = KardexEntry.objects.create(
        organization=organization,
        variant=variant,
        type=movement_type,
        qty=qty,
        unit_cost=unit_cost,
        note=note,
        reference=reference,
        created_by=user,
    )
    entry.apply_to_stock()
    return entry
