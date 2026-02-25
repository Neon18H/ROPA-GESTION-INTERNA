from unittest.mock import patch

from django.contrib.messages.storage.fallback import FallbackStorage
from django.contrib.messages.middleware import MessageMiddleware
from django.contrib.sessions.middleware import SessionMiddleware
from django.db import IntegrityError
from django.test import RequestFactory, TestCase
from django.urls import reverse

from apps.accounts.models import Organization, User
from apps.inventory.models import Product, Variant
from apps.inventory.views import ProductUpdateView


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
            },
        )

        self.assertEqual(response.status_code, 302)
        self.product.refresh_from_db()
        self.assertEqual(self.product.name, 'Producto editado')

    def test_post_handles_integrity_error_and_shows_field_error(self):
        url = reverse('inventory:product_update', kwargs={'pk': self.product.pk})

        with patch('apps.inventory.views.ProductUpdateForm.save', side_effect=IntegrityError('uq_org_sku')):
            response = self.client.post(
                url,
                {
                    'sku': 'SKU-001',
                    'name': 'Producto editado',
                    'description': 'Descripcion',
                    'is_active': 'on',
                },
            )

        self.assertEqual(response.status_code, 200)
        self.assertFormError(response, 'form', 'sku', 'SKU ya existe')

    def test_request_factory_with_session_and_messages_captures_exception_and_avoids_500(self):
        factory = RequestFactory()
        request = factory.post(
            reverse('inventory:product_update', kwargs={'pk': self.product.pk}),
            data={
                'sku': 'SKU-001',
                'name': 'Producto editado',
                'description': 'Descripcion',
                'is_active': 'on',
            },
        )
        request.user = self.user

        session_middleware = SessionMiddleware(lambda req: None)
        session_middleware.process_request(request)
        request.session.save()

        message_middleware = MessageMiddleware(lambda req: None)
        message_middleware.process_request(request)
        setattr(request, '_messages', FallbackStorage(request))

        with patch('apps.inventory.views.ProductUpdateView.form_valid', side_effect=RuntimeError('boom')):
            with patch('apps.inventory.views.logger.exception') as mocked_exception:
                response = ProductUpdateView.as_view()(request, pk=self.product.pk)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(mocked_exception.called)
        self.assertIn(
            'Ocurrió un error inesperado al actualizar el producto.',
            response.rendered_content,
        )
