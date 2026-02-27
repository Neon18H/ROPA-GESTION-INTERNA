from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse

from apps.accounts.models import Organization, User
from apps.inventory.models import KardexEntry, Product, Variant


class ProductDeleteViewTests(TestCase):
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
            sku='SKU-DEL',
            name='Producto borrable',
        )
        self.variant = Variant.objects.create(
            product=self.product,
            size='UNICA',
            color='UNICO',
            gender=Variant.Gender.UNISEX,
        )

    def test_delete_view_blocks_get(self):
        self.client.force_login(self.user)
        url = reverse('inventory:product_delete', kwargs={'pk': self.product.pk})

        response = self.client.get(url)

        self.assertEqual(response.status_code, 405)

    def test_delete_hard_deletes_product_when_has_no_links(self):
        self.client.force_login(self.user)
        url = reverse('inventory:product_delete', kwargs={'pk': self.product.pk})

        with patch('apps.inventory.views.Product.image.delete') as image_delete:
            response = self.client.post(url)

        self.assertEqual(response.status_code, 302)
        self.assertFalse(Product.objects.filter(pk=self.product.pk).exists())
        image_delete.assert_not_called()

    def test_delete_soft_deletes_when_product_has_kardex_links(self):
        self.client.force_login(self.user)
        KardexEntry.objects.create(
            organization=self.organization,
            variant=self.variant,
            type=KardexEntry.Type.IN,
            qty=1,
            unit_cost=0,
            created_by=self.user,
        )
        url = reverse('inventory:product_delete', kwargs={'pk': self.product.pk})

        with patch('apps.inventory.views.Product.image.delete') as image_delete:
            response = self.client.post(url)

        self.assertEqual(response.status_code, 302)
        self.product.refresh_from_db()
        self.assertFalse(self.product.is_active)
        image_delete.assert_not_called()

    def test_delete_is_scoped_by_organization(self):
        self.client.force_login(self.other_user)
        url = reverse('inventory:product_delete', kwargs={'pk': self.product.pk})

        response = self.client.post(url)

        self.assertEqual(response.status_code, 404)
