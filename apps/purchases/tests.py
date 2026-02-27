from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from apps.accounts.models import Organization, User
from apps.inventory.models import Product, Stock, Variant
from apps.purchases.models import PurchaseOrder, Supplier


class PurchaseFlowTests(TestCase):
    def setUp(self):
        self.org = Organization.objects.create(name='Org')
        self.other_org = Organization.objects.create(name='Other Org')
        self.user = User.objects.create_user(username='pur', password='pass1234', organization=self.org, role=User.Role.ADMIN)
        self.other_user = User.objects.create_user(username='pur2', password='pass1234', organization=self.other_org, role=User.Role.ADMIN)
        self.product = Product.objects.create(organization=self.org, sku='SKU-1', name='Prod 1')
        self.variant = Variant.objects.create(product=self.product, size='M', color='Negro', gender=Variant.Gender.UNISEX, price=100)
        Stock.objects.create(variant=self.variant, quantity=2, avg_cost=Decimal('10.00'))

    def test_variant_str_label(self):
        label = str(self.variant)
        self.assertIn('SKU-1 - Prod 1', label)
        self.assertIn('Talla: M', label)
        self.assertNotIn('Variant object', label)

    def test_create_supplier_redirects(self):
        self.client.force_login(self.user)

        response = self.client.post(
            reverse('purchases:supplier_create'),
            {'name': 'Prov 1', 'phone': '123', 'email': 'prov@example.com', 'address': '', 'notes': '', 'is_active': 'on'},
        )

        self.assertEqual(response.status_code, 302)
        self.assertTrue(Supplier.objects.filter(organization=self.org, name='Prov 1').exists())

    def test_purchase_creates_stock_updates_cost(self):
        supplier = Supplier.objects.create(organization=self.org, name='Prov', is_active=True)
        self.client.force_login(self.user)
        create_payload = {
            'supplier': supplier.pk,
            'notes': 'lote',
            'items-TOTAL_FORMS': '1',
            'items-INITIAL_FORMS': '0',
            'items-MIN_NUM_FORMS': '0',
            'items-MAX_NUM_FORMS': '1000',
            'items-0-variant': str(self.variant.pk),
            'items-0-qty': '5',
            'items-0-unit_cost': '20.00',
        }

        create_response = self.client.post(reverse('purchases:create'), create_payload)
        self.assertEqual(create_response.status_code, 302)

        order = PurchaseOrder.objects.get(organization=self.org)
        stock = Stock.objects.get(variant=self.variant)
        self.assertEqual(stock.quantity, 7)
        self.assertEqual(order.status, PurchaseOrder.Status.RECEIVED)
        self.assertEqual(stock.last_cost, Decimal('20.00'))

    def test_purchase_manual_variant_creates_product_variant_in_org_only(self):
        supplier = Supplier.objects.create(organization=self.org, name='Prov', is_active=True)
        other_supplier = Supplier.objects.create(organization=self.other_org, name='Prov2', is_active=True)

        self.client.force_login(self.user)
        response = self.client.post(
            reverse('purchases:ajax_create_variant'),
            {
                'supplier': supplier.pk,
                'sku': 'SKU-N',
                'product_name': 'Nuevo',
                'size': 'L',
                'color': 'Azul',
                'gender': Variant.Gender.HOMBRE,
                'barcode': 'BC001',
                'unit_cost': '30.00',
                'qty': '2',
            },
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(Product.objects.filter(organization=self.org, sku='SKU-N').exists())
        self.assertTrue(Variant.objects.filter(product__organization=self.org, id=payload['variant_id']).exists())

        bad_response = self.client.post(
            reverse('purchases:ajax_create_variant'),
            {
                'supplier': other_supplier.pk,
                'sku': 'SKU-X',
                'product_name': 'Prohibido',
                'unit_cost': '10.00',
                'qty': '1',
            },
        )
        self.assertEqual(bad_response.status_code, 400)
        self.assertFalse(Product.objects.filter(organization=self.org, sku='SKU-X').exists())
