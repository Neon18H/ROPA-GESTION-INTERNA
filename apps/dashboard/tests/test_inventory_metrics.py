from decimal import Decimal

from django.test import TestCase

from apps.accounts.models import Organization
from apps.dashboard.services import get_inventory_metrics
from apps.inventory.models import Product, ProductStock, Stock, Variant


class InventoryMetricsTests(TestCase):
    def test_uses_variant_stock_and_prefers_variant_sale_price(self):
        org = Organization.objects.create(name='Org A')
        other_org = Organization.objects.create(name='Org B')

        product_a = Product.objects.create(organization=org, sku='A-1', name='Prod A', suggested_price=Decimal('100.00'))
        product_b = Product.objects.create(organization=org, sku='B-1', name='Prod B', suggested_price=Decimal('50.00'))
        other_product = Product.objects.create(
            organization=other_org,
            sku='C-1',
            name='Prod C',
            suggested_price=Decimal('999.00'),
        )

        ProductStock.objects.create(organization=org, product=product_a, qty=999)
        ProductStock.objects.create(organization=org, product=product_b, qty=999)
        ProductStock.objects.create(organization=other_org, product=other_product, qty=99)

        variant_a1 = Variant.objects.create(product=product_a, size='M', color='Negro')
        variant_a2 = Variant.objects.create(product=product_a, size='L', color='Negro')
        variant_b1 = Variant.objects.create(
            product=product_b,
            size='U',
            color='Azul',
            default_sale_price=Decimal('80.00'),
        )
        Stock.objects.create(variant=variant_a1, quantity=7, min_alert=3)
        Stock.objects.create(variant=variant_a2, quantity=5, min_alert=3)
        Stock.objects.create(variant=variant_b1, quantity=12, min_alert=3)

        metrics = get_inventory_metrics(org)

        self.assertEqual(metrics['stock_total'], 24)
        self.assertEqual(metrics['inventory_value'], Decimal('1560.00'))
