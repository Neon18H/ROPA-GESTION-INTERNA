from django.core.management.base import BaseCommand, CommandError
from django.db.models import Max

from apps.accounts.models import Organization
from apps.inventory.models import Product, ProductStock, Stock


class Command(BaseCommand):
    help = 'Migra stock por variante al pool de stock por producto para una organización.'

    def add_arguments(self, parser):
        parser.add_argument('--org', type=int, required=True, help='ID de organización')
        parser.add_argument('--dry-run', action='store_true', help='Solo mostrar cambios sin guardar')

    def handle(self, *args, **options):
        org_id = options['org']
        dry_run = options['dry_run']

        try:
            organization = Organization.objects.get(pk=org_id)
        except Organization.DoesNotExist as exc:
            raise CommandError(f'No existe la organización {org_id}.') from exc

        products = Product.objects.filter(organization=organization)
        created = 0
        updated = 0

        for product in products:
            qty_base = (
                Stock.objects.filter(variant__product=product)
                .aggregate(max_qty=Max('quantity'))
                .get('max_qty')
                or 0
            )

            stock = ProductStock.objects.filter(organization=organization, product=product).first()
            if stock is None:
                created += 1
                if not dry_run:
                    ProductStock.objects.create(organization=organization, product=product, qty=qty_base)
                continue

            if stock.qty != qty_base:
                updated += 1
                if not dry_run:
                    stock.qty = qty_base
                    stock.save(update_fields=['qty'])

        action = 'DRY RUN' if dry_run else 'APLICADO'
        self.stdout.write(self.style.SUCCESS(f'[{action}] Organización={org_id} | creados={created} | actualizados={updated}'))
