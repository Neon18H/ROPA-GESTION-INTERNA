from unittest.mock import patch

from django.db import IntegrityError
from django.test import TestCase
from django.urls import reverse

from apps.accounts.models import Organization, User
from apps.inventory.models import Product, ProductStock, Variant


class ProductUpdateViewTenantTests(TestCase):
    def setUp(self):
        self.organization = Organization.objects.create(name='Org 1')
        self.other_organization = Organization.objects.create(name='Org 2')
        self.user = User.objects.create_user(
            username='admin1',
            password='pass1234',
            organization=self.organization,
            role=User.Role.ADMIN,
        )
        self.other_user = User.objects.create_user(
            username='admin2',
            password='pass1234',
            organization=self.other_organization,
            role=User.Role.ADMIN,
        )
        self.product = Product.objects.create(
            organization=self.organization,
            sku='SKU-001',
            name='Producto original',
        )
        self.variant = Variant.objects.create(product=self.product, size='UNICA', color='UNICO', gender=Variant.Gender.UNISEX, price=10, default_sale_price=10)
        ProductStock.objects.create(organization=self.organization, product=self.product, qty=3)
        self.client.force_login(self.user)

    def _payload(self):
        return {
            'sku': 'SKU-001',
            'name': 'Producto editado',
            'description': 'Descripcion',
            'is_active': 'on',
            'variants-TOTAL_FORMS': '1',
            'variants-INITIAL_FORMS': '1',
            'variants-MIN_NUM_FORMS': '0',
            'variants-MAX_NUM_FORMS': '1000',
            'variants-0-id': str(self.variant.id),
            'variants-0-size': 'M',
            'variants-0-color': 'Negro',
            'variants-0-gender': Variant.Gender.UNISEX,
            'variants-0-barcode': 'BAR-001',
            'variants-0-default_sale_price': '19.90',
            'variants-0-is_active': 'on',
        }

    def test_get_edit_returns_200_for_same_org_product(self):
        url = reverse('inventory:product_update', kwargs={'pk': self.product.pk})

        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

    def test_post_edit_returns_302_for_same_org_product(self):
        url = reverse('inventory:product_update', kwargs={'pk': self.product.pk})

        response = self.client.post(url, self._payload())

        self.assertEqual(response.status_code, 302)
        self.product.refresh_from_db()
        self.variant.refresh_from_db()
        self.assertEqual(self.product.name, 'Producto editado')
        self.assertEqual(self.variant.default_sale_price, self.variant.default_sale_price.__class__('19.90'))

    def test_post_handles_integrity_error_and_shows_field_error(self):
        url = reverse('inventory:product_update', kwargs={'pk': self.product.pk})

        with patch('apps.inventory.views.ProductUpdateForm.save', side_effect=IntegrityError('uq_org_sku')):
            response = self.client.post(url, self._payload())

        self.assertEqual(response.status_code, 200)
        self.assertFormError(response, 'form', 'sku', 'SKU ya existe')

    def test_other_org_cannot_edit_product(self):
        self.client.force_login(self.other_user)
        url = reverse('inventory:product_update', kwargs={'pk': self.product.pk})

        response = self.client.get(url)

        self.assertEqual(response.status_code, 404)

    def test_invalid_variant_formset_returns_200_with_errors(self):
        url = reverse('inventory:product_update', kwargs={'pk': self.product.pk})
        payload = self._payload()
        payload['variants-0-default_sale_price'] = '-1'

        response = self.client.post(url, payload)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'precio sugerido no puede ser negativo', status_code=200)


    def test_edit_does_not_reapply_initial_stock(self):
        url = reverse('inventory:product_update', kwargs={'pk': self.product.pk})

        response = self.client.post(url, self._payload())

        self.assertEqual(response.status_code, 302)
        stock = ProductStock.objects.get(organization=self.organization, product=self.product)
        self.assertEqual(stock.qty, 3)

    def test_add_variant_keeps_single_product_stock_pool(self):
        url = reverse('inventory:product_update', kwargs={'pk': self.product.pk})
        payload = self._payload()
        payload.update(
            {
                'variants-TOTAL_FORMS': '2',
                'variants-1-id': '',
                'variants-1-size': 'L',
                'variants-1-color': 'Azul',
                'variants-1-gender': Variant.Gender.HOMBRE,
                'variants-1-barcode': 'BAR-NEW',
                'variants-1-default_sale_price': '49.99',
                'variants-1-is_active': 'on',
            }
        )

        response = self.client.post(url, payload)

        self.assertEqual(response.status_code, 302)
        self.assertTrue(Variant.objects.filter(product=self.product, barcode='BAR-NEW').exists())
        self.assertEqual(ProductStock.objects.filter(organization=self.organization, product=self.product).count(), 1)
