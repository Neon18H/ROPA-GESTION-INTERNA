from django.test import TestCase
from django.urls import reverse

from apps.accounts.models import Organization, User
from apps.inventory.models import Brand, Category, Product, ProductStock, Variant
from apps.settings_app.models import StoreSettings


class ProductGalleryViewTests(TestCase):
    def setUp(self):
        self.organization = Organization.objects.create(name='Org Gallery')
        self.other_organization = Organization.objects.create(name='Org Other')
        self.user = User.objects.create_user(
            username='gallery-admin',
            password='pass1234',
            organization=self.organization,
            role=User.Role.ADMIN,
        )
        StoreSettings.objects.create(organization_id=self.organization.id, low_stock_default=4)

        self.category = Category.objects.create(organization=self.organization, name='Chaquetas')
        self.brand = Brand.objects.create(organization=self.organization, name='Acme')
        self.product = Product.objects.create(
            organization=self.organization,
            sku='SKU-GAL-1',
            name='Chaqueta Azul',
            category=self.category,
            brand=self.brand,
            is_active=True,
        )
        variant = Variant.objects.create(product=self.product, size='M', color='Azul', is_active=True)
        ProductStock.objects.create(organization=self.organization, product=self.product, qty=2)

        other_category = Category.objects.create(organization=self.other_organization, name='Pantalones')
        other_brand = Brand.objects.create(organization=self.other_organization, name='Marca X')
        other_product = Product.objects.create(
            organization=self.other_organization,
            sku='SKU-OTH-1',
            name='Pantalón Negro',
            category=other_category,
            brand=other_brand,
            is_active=True,
        )
        other_variant = Variant.objects.create(product=other_product, size='L', color='Negro', is_active=True)
        ProductStock.objects.create(organization=self.other_organization, product=other_product, qty=99)

        self.client.force_login(self.user)

    def test_gallery_view_returns_200_and_uses_org_scope(self):
        response = self.client.get(reverse('inventory:product_gallery'))

        self.assertEqual(response.status_code, 200)
        variants = list(response.context['variants'])
        self.assertEqual(len(variants), 1)
        self.assertEqual(variants[0].product_id, self.product.id)

    def test_gallery_filters_category_brand_and_query(self):
        response = self.client.get(
            reverse('inventory:product_gallery'),
            {'category': self.category.id, 'brand': self.brand.id, 'q': 'Azul'},
        )

        self.assertEqual(response.status_code, 200)
        variants = list(response.context['variants'])
        self.assertEqual(len(variants), 1)
        self.assertEqual(variants[0].stock_qty, 2)
