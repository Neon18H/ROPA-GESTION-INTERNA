from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from apps.accounts.models import Organization, User
from apps.customers.models import Customer
from apps.inventory.models import Product, Variant
from apps.sales.models import Sale, SaleItem
from apps.sales.utils import compute_sale_totals
from apps.settings_app.models import StoreSettings


class BillingInvoiceTests(TestCase):
    databases = {'default', 'settings_db'}
    def setUp(self):
        self.org = Organization.objects.create(name='Org Factura', nit='123')
        self.user = User.objects.create_user(
            username='billing-admin',
            password='pass1234',
            organization=self.org,
            role=User.Role.ADMIN,
        )
        self.customer = Customer.objects.create(organization=self.org, name='Cliente Demo')
        self.product = Product.objects.create(organization=self.org, sku='SKU-1', name='Camisa')
        self.variant = Variant.objects.create(product=self.product, size='M', color='Azul', price=Decimal('100.00'))
        self.sale = Sale.objects.create(organization=self.org, number=1, customer=self.customer, created_by=self.user)

    def test_receipt_renders_with_billing_settings(self):
        StoreSettings.objects.using('settings_db').create(
            organization_id=self.org.id,
            billing_legal_name='Mi Empresa SAS',
            billing_tax_id='900123123-4',
            billing_vat_rate=Decimal('19.00'),
        )
        SaleItem.objects.create(
            sale=self.sale,
            variant=self.variant,
            qty=2,
            unit_price=Decimal('100.00'),
            tax_rate=None,
            discount=Decimal('0.00'),
            line_total=Decimal('238.00'),
        )

        self.client.force_login(self.user)
        response = self.client.get(reverse('sales:receipt', kwargs={'pk': self.sale.pk}))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Mi Empresa SAS')
        self.assertContains(response, 'IVA (19.00%)')

    def test_compute_sale_totals_decimal_safe(self):
        class Item:
            def __init__(self, unit_price, qty, tax_rate=None):
                self.unit_price = unit_price
                self.qty = qty
                self.tax_rate = tax_rate

        items = [
            Item(Decimal('100.00'), 2, None),
            Item(Decimal('50.00'), 1, Decimal('5.00')),
        ]

        result = compute_sale_totals(items, default_vat_rate=Decimal('19.00'))

        self.assertEqual(result['subtotal'], Decimal('250.00'))
        self.assertEqual(result['tax_total'], Decimal('40.50'))
        self.assertEqual(result['total'], Decimal('290.50'))
