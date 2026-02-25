from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from apps.accounts.models import Organization, User
from apps.inventory.models import Product, Stock, Variant
from apps.purchases.models import PurchaseOrder, Supplier


class PurchaseFlowTests(TestCase):
    def setUp(self):
        self.org = Organization.objects.create(name='Org')
        self.user = User.objects.create_user(username='pur', password='pass1234', organization=self.org, role=User.Role.ADMIN)
        self.product = Product.objects.create(organization=self.org, sku='SKU-1', name='Prod 1')
        self.variant = Variant.objects.create(product=self.product, size='M', color='Negro', gender=Variant.Gender.UNISEX, price=100)
        Stock.objects.create(variant=self.variant, quantity=2, avg_cost=Decimal('10.00'))

    def test_create_supplier_redirects(self):
        self.client.force_login(self.user)

        response = self.client.post(
            reverse('purchases:supplier_create'),
            {'name': 'Prov 1', 'phone': '123', 'email': 'prov@example.com', 'address': '', 'notes': '', 'is_active': 'on'},
        )

        self.assertEqual(response.status_code, 302)
        self.assertTrue(Supplier.objects.filter(organization=self.org, name='Prov 1').exists())

    def test_create_purchase_and_receive_updates_stock(self):
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
        receive_response = self.client.post(reverse('purchases:receive', kwargs={'pk': order.pk}))
        self.assertEqual(receive_response.status_code, 302)

        stock = Stock.objects.get(variant=self.variant)
        self.assertEqual(stock.quantity, 7)
        self.assertEqual(order.status, PurchaseOrder.Status.DRAFT)
        order.refresh_from_db()
        self.assertEqual(order.status, PurchaseOrder.Status.RECEIVED)
