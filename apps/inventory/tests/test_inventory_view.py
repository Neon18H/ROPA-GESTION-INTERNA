from django.test import TestCase
from django.urls import reverse

from apps.accounts.models import Organization, User
from apps.inventory.models import Product, ProductStock, Stock, Variant


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
        self.variant_two = Variant.objects.create(product=product, size='S', color='Azul', gender=Variant.Gender.MUJER)
        ProductStock.objects.create(organization=self.organization, product=product, qty=11)
        Stock.objects.create(variant=self.variant, quantity=5)
        Stock.objects.create(variant=self.variant_two, quantity=6)

        other_product = Product.objects.create(organization=self.other_organization, sku='SKU-OTH', name='Other')
        other_variant = Variant.objects.create(product=other_product, size='L', color='Negro', gender=Variant.Gender.MUJER)
        ProductStock.objects.create(organization=self.other_organization, product=other_product, qty=99)
        Stock.objects.create(variant=other_variant, quantity=99)

        self.client.force_login(self.user)

    def test_inventory_lists_variants_with_gender_and_org_scope(self):
        response = self.client.get(reverse('inventory:inventory'))

        self.assertEqual(response.status_code, 200)
        variants = list(response.context['variants'])
        self.assertEqual(len(variants), 2)
        self.assertEqual({v.id for v in variants}, {self.variant.id, self.variant_two.id})
        self.assertContains(response, 'Hombre')
        self.assertContains(response, 'Mujer')

    def test_inventory_uses_variant_stock_quantity_instead_of_product_stock(self):
        response = self.client.get(reverse('inventory:inventory'))

        self.assertEqual(response.status_code, 200)
        quantities = {variant.id: variant.stock_qty_value for variant in response.context['variants']}
        self.assertEqual(quantities[self.variant.id], 5)
        self.assertEqual(quantities[self.variant_two.id], 6)
        self.assertContains(response, 'OK · 5')
        self.assertContains(response, 'OK · 6')
