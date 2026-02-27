from django.core.management import call_command
from django.test import TestCase

from apps.accounts.models import Organization
from apps.inventory.models import Product, ProductStock, Stock, Variant


class InventoryBackfillVariantStockCommandTests(TestCase):
    def test_creates_missing_variant_stock_using_product_stock_qty(self):
        org = Organization.objects.create(name='Org A')
        product = Product.objects.create(organization=org, sku='SKU-A', name='Producto A')
        ProductStock.objects.create(organization=org, product=product, qty=10)

        variant_1 = Variant.objects.create(product=product, size='M', color='Negro')
        variant_2 = Variant.objects.create(product=product, size='L', color='Azul')
        Stock.objects.create(variant=variant_1, quantity=4)

        call_command('inventory_backfill_variant_stock')

        self.assertEqual(Stock.objects.get(variant=variant_1).quantity, 4)
        self.assertEqual(Stock.objects.get(variant=variant_2).quantity, 10)

        call_command('inventory_backfill_variant_stock')
        self.assertEqual(Stock.objects.filter(variant__product=product).count(), 2)

    def test_filters_backfill_by_organization_id(self):
        org_a = Organization.objects.create(name='Org A')
        org_b = Organization.objects.create(name='Org B')

        product_a = Product.objects.create(organization=org_a, sku='SKU-A', name='Producto A')
        product_b = Product.objects.create(organization=org_b, sku='SKU-B', name='Producto B')

        ProductStock.objects.create(organization=org_a, product=product_a, qty=7)
        ProductStock.objects.create(organization=org_b, product=product_b, qty=12)

        variant_a = Variant.objects.create(product=product_a, size='S', color='Verde')
        variant_b = Variant.objects.create(product=product_b, size='M', color='Rojo')

        call_command('inventory_backfill_variant_stock', organization_id=org_a.id)

        self.assertTrue(Stock.objects.filter(variant=variant_a, quantity=7).exists())
        self.assertFalse(Stock.objects.filter(variant=variant_b).exists())
