from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from apps.accounts.models import Organization, User
from apps.settings_app.models import StoreSettings


class DashboardViewTests(TestCase):
    def test_root_url_renders_for_logged_in_user(self):
        org = Organization.objects.create(name='Org')
        user = User.objects.create_user(username='root', password='pass1234', organization=org, role=User.Role.ADMIN)

        self.assertTrue(self.client.login(username='root', password='pass1234'))
        response = self.client.get('/')

        self.assertEqual(response.status_code, 200)

    def test_dashboard_renders_without_sales_data(self):
        org = Organization.objects.create(name='Org')
        user = User.objects.create_user(username='dash', password='pass1234', organization=org, role=User.Role.ADMIN)
        self.client.force_login(user)

        response = self.client.get(reverse('dashboard:index'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Ventas últimos 30 días')


class DashboardDualCurrencyTests(TestCase):
    databases = {'default', 'settings_db'}

    def test_dual_currency_render_dashboard(self):
        org = Organization.objects.create(name='Org FX')
        user = User.objects.create_user(username='dashfx', password='pass1234', organization=org, role=User.Role.ADMIN)
        StoreSettings.objects.using('settings_db').create(
            organization_id=org.id,
            fx_usd_cop_rate=Decimal('4000.000000'),
            show_dual_currency=True,
        )

        self.client.force_login(user)
        response = self.client.get(reverse('dashboard:index'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'US$')


class RoadmapViewTests(TestCase):
    def test_roadmap_requires_login(self):
        response = self.client.get(reverse('dashboard:roadmap'))

        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('accounts:login'), response.url)

    def test_roadmap_renders_for_authenticated_user(self):
        org = Organization.objects.create(name='Roadmap Org')
        user = User.objects.create_user(username='roadmap', password='pass1234', organization=org, role=User.Role.ADMIN)
        self.client.force_login(user)

        response = self.client.get(reverse('dashboard:roadmap'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '🚀 Roadmap del Producto')
        self.assertContains(response, 'Testing del servicio de correos')
