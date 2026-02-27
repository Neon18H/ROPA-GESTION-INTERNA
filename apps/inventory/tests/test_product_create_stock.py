from django.test import TestCase
from django.urls import reverse

from apps.accounts.models import Organization, User
from apps.inventory.models import Product, ProductStock


class ProductCreateInitialStockTests(TestCase):
    def setUp(self):
        self.organization = Organization.objects.create(name='Org Stock')
        self.user = User.objects.create_user(
            username='stock-admin',
            password='pass1234',
            organization=self.organization,
            role=User.Role.ADMIN,
        )
        self.client.force_login(self.user)

    def test_initial_qty_is_applied_to_product_pool_stock(self):
        response = self.client.post(
            reverse('inventory:product_create'),
            {
                'sku': 'SKU-STOCK-1',
                'name': 'Producto con variantes',
                'description': 'Demo',
                'is_active': 'on',
                'initial_qty': '10',
                'initial_cost': '25.00',
                'initial_sale_price': '40.00',
                'variants-TOTAL_FORMS': '2',
                'variants-INITIAL_FORMS': '0',
                'variants-MIN_NUM_FORMS': '0',
                'variants-MAX_NUM_FORMS': '1000',
                'variants-0-size': 'M',
                'variants-0-color': 'Negro',
                'variants-0-gender': 'HOMBRE',
                'variants-0-barcode': 'BC-01',
                'variants-1-size': 'L',
                'variants-1-color': 'Azul',
                'variants-1-gender': 'MUJER',
                'variants-1-barcode': 'BC-02',
            },
        )

        self.assertEqual(response.status_code, 302)
        product = Product.objects.get(organization=self.organization, sku='SKU-STOCK-1')
        stock = ProductStock.objects.get(organization=self.organization, product=product)
        self.assertEqual(stock.qty, 10)
