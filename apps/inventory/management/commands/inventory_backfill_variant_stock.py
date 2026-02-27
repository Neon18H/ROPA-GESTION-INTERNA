from django.core.management.base import BaseCommand
from django.db.models import OuterRef, Subquery

from apps.inventory.models import ProductStock, Stock, Variant


class Command(BaseCommand):
    help = 'Crea filas faltantes de Stock por variante usando ProductStock.qty como base cuando exista.'

    def add_arguments(self, parser):
        parser.add_argument('--organization-id', type=int, help='ID de organización para limitar el backfill.')

    def handle(self, *args, **options):
        organization_id = options.get('organization_id')

        variants = Variant.objects.filter(stock__isnull=True).select_related('product')
        if organization_id:
            variants = variants.filter(product__organization_id=organization_id)

        product_stock_qty = ProductStock.objects.filter(
            organization_id=OuterRef('product__organization_id'),
            product_id=OuterRef('product_id'),
        ).values('qty')[:1]

        variants = variants.annotate(product_initial_qty=Subquery(product_stock_qty))

        created = 0
        for variant in variants.iterator():
            qty = variant.product_initial_qty if variant.product_initial_qty is not None else 0
            _, was_created = Stock.objects.get_or_create(
                variant=variant,
                defaults={'quantity': qty},
            )
            if was_created:
                created += 1

        scope = f'organization_id={organization_id}' if organization_id else 'all_organizations'
        self.stdout.write(self.style.SUCCESS(f'Backfill completado ({scope}). Stocks creados: {created}.'))
