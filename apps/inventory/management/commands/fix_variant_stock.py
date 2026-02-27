from django.core.management.base import BaseCommand, CommandError
from django.db.models import Max

from apps.accounts.models import Organization
from apps.inventory.models import Product, Stock, Variant


class Command(BaseCommand):
    help = 'Repara stock faltante o en cero para variantes de una organización.'

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

        products = Product.objects.filter(organization=organization).prefetch_related('variant_set')
        created_count = 0
        repaired_count = 0

        for product in products:
            qty_base = (
                Stock.objects.filter(variant__product=product)
                .aggregate(max_qty=Max('quantity'))
                .get('max_qty')
                or 0
            )

            variants = Variant.objects.filter(product=product)
            for variant in variants:
                stock = Stock.objects.filter(variant=variant).first()
                if stock is None:
                    created_count += 1
                    if not dry_run:
                        Stock.objects.create(variant=variant, quantity=qty_base)
                    continue

                if stock.quantity == 0 and qty_base > 0:
                    repaired_count += 1
                    if not dry_run:
                        stock.quantity = qty_base
                        stock.save(update_fields=['quantity'])

        action = 'DRY RUN' if dry_run else 'APLICADO'
        self.stdout.write(
            self.style.SUCCESS(
                f'[{action}] Organización={org_id} | stocks creados={created_count} | stocks reparados={repaired_count}'
            )
        )
