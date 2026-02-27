from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from apps.accounts.models import Organization, User
from apps.customers.models import Customer
from apps.inventory.models import Product, ProductStock, Variant
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
        self.variant = Variant.objects.create(product=self.product, size='M', color='Azul', price=Decimal('100.00'), default_sale_price=Decimal('100.00'))
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


class POSCustomerModesTests(TestCase):
    databases = {'default', 'settings_db'}

    def setUp(self):
        self.org = Organization.objects.create(name='Org POS', nit='900')
        self.other_org = Organization.objects.create(name='Org Other', nit='901')
        self.user = User.objects.create_user(
            username='pos-admin',
            password='pass1234',
            organization=self.org,
            role=User.Role.ADMIN,
        )
        self.product = Product.objects.create(organization=self.org, sku='SKU-2', name='Pantalón')
        self.variant = Variant.objects.create(product=self.product, size='L', color='Negro', price=Decimal('90.00'), default_sale_price=Decimal('90.00'))
        ProductStock.objects.create(organization=self.org, product=self.product, qty=15)
        self.customer = Customer.objects.create(organization=self.org, name='Cliente Existente')

    def _payload(self, **overrides):
        data = {
            'customer_mode': 'existing',
            'customer': str(self.customer.pk),
            'payment_method': 'CASH',
            'items-TOTAL_FORMS': '1',
            'items-INITIAL_FORMS': '0',
            'items-MIN_NUM_FORMS': '0',
            'items-MAX_NUM_FORMS': '1000',
            'items-0-variant': str(self.variant.pk),
            'items-0-quantity': '2',
            'items-0-unit_price': '90.00',
            'items-0-tax_rate': '0',
            'items-0-discount': '0',
        }
        data.update(overrides)
        return data

    def test_pos_get_ok(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse('sales:pos'))
        self.assertEqual(response.status_code, 200)


    def test_pos_get_includes_default_sale_price_data(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse('sales:pos'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'data-default-sale-price="90.00"')

    def test_pos_post_existing_customer_creates_sale(self):
        self.client.force_login(self.user)
        response = self.client.post(reverse('sales:pos'), data=self._payload())

        self.assertEqual(response.status_code, 302)
        sale = Sale.objects.latest('id')
        self.assertEqual(sale.customer_id, self.customer.id)
        self.assertEqual(sale.organization_id, self.org.id)
        self.assertEqual(ProductStock.objects.get(organization=self.org, product=self.product).qty, 13)

    def test_pos_manual_unit_price_override_is_persisted(self):
        self.client.force_login(self.user)
        response = self.client.post(reverse('sales:pos'), data=self._payload(**{'items-0-unit_price': '120.00'}))

        self.assertEqual(response.status_code, 302)
        sale_item = SaleItem.objects.latest('id')
        self.assertEqual(sale_item.unit_price, Decimal('120.00'))

    def test_pos_post_new_customer_creates_customer_and_sale(self):
        self.client.force_login(self.user)
        response = self.client.post(
            reverse('sales:pos'),
            data=self._payload(
                customer_mode='new',
                customer='',
                new_customer_name='Cliente Nuevo',
                new_customer_document='CC123',
                new_customer_phone='3000000000',
                new_customer_email='nuevo@example.com',
                new_customer_address='Calle 123',
            ),
        )

        self.assertEqual(response.status_code, 302)
        sale = Sale.objects.latest('id')
        self.assertEqual(sale.organization_id, self.org.id)
        self.assertEqual(sale.customer.organization_id, self.org.id)
        self.assertEqual(sale.customer.name, 'Cliente Nuevo')
        self.assertIn('Calle 123', sale.customer.notes)

    def test_pos_post_new_customer_without_name_shows_error(self):
        self.client.force_login(self.user)
        response = self.client.post(
            reverse('sales:pos'),
            data=self._payload(customer_mode='new', customer='', new_customer_name=''),
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'El nombre del cliente es obligatorio.')
