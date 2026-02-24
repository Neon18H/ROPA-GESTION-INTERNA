from django.test import TestCase
from django.urls import reverse

from apps.accounts.models import Organization, User
from apps.inventory.models import Product, Variant


class ProductUpdateViewTenantTests(TestCase):
    def setUp(self):
        self.organization = Organization.objects.create(name='Org 1')
        self.user = User.objects.create_user(
            username='admin1',
            password='pass1234',
            organization=self.organization,
            role=User.Role.ADMIN,
        )
        self.product = Product.objects.create(
            organization=self.organization,
            sku='SKU-001',
            name='Producto original',
        )
        Variant.objects.create(product=self.product, size='UNICA', color='UNICO', gender=Variant.Gender.UNISEX)
        self.client.force_login(self.user)

    def test_get_edit_returns_200_for_same_org_product(self):
        url = reverse('inventory:product_update', kwargs={'pk': self.product.pk})

        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

    def test_post_edit_returns_302_for_same_org_product(self):
        url = reverse('inventory:product_update', kwargs={'pk': self.product.pk})

        response = self.client.post(
            url,
            {
                'sku': 'SKU-001',
                'name': 'Producto editado',
                'description': 'Descripcion',
                'is_active': 'on',
                'variants-TOTAL_FORMS': '1',
                'variants-INITIAL_FORMS': '0',
                'variants-MIN_NUM_FORMS': '0',
                'variants-MAX_NUM_FORMS': '1000',
                'variants-0-size': 'UNICA',
                'variants-0-color': 'UNICO',
                'variants-0-gender': Variant.Gender.UNISEX,
                'variants-0-barcode': '',
            },
        )

        self.assertEqual(response.status_code, 302)
        self.product.refresh_from_db()
        self.assertEqual(self.product.name, 'Producto editado')
