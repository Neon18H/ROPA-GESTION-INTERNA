from django.test import TestCase
from django.urls import reverse

from apps.accounts.models import Organization, User
from apps.inventory.models import Product, ProductStock, Variant


class InventoryViewTests(TestCase):
    def setUp(self):
        self.organization = Organization.objects.create(name='Org Inventory')
        self.other_organization = Organization.objects.create(name='Other Org')
        self.user = User.objects.create_user(
            username='inventory-admin',
            password='pass1234',
            organization=self.organization,
            role=User.Role.ADMIN,
        )

        product = Product.objects.create(organization=self.organization, sku='SKU-INV', name='Polo')
        self.variant = Variant.objects.create(product=product, size='M', color='Rojo', gender=Variant.Gender.HOMBRE)
        ProductStock.objects.create(organization=self.organization, product=product, qty=5)

        other_product = Product.objects.create(organization=self.other_organization, sku='SKU-OTH', name='Other')
        other_variant = Variant.objects.create(product=other_product, size='L', color='Negro', gender=Variant.Gender.MUJER)
        ProductStock.objects.create(organization=self.other_organization, product=other_product, qty=99)

        self.client.force_login(self.user)

    def test_inventory_lists_variants_with_gender_and_org_scope(self):
        response = self.client.get(reverse('inventory:inventory'))

        self.assertEqual(response.status_code, 200)
        variants = list(response.context['variants'])
        self.assertEqual(len(variants), 1)
        self.assertEqual(variants[0].id, self.variant.id)
        self.assertContains(response, 'Hombre')
