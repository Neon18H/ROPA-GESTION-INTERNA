from django.test import TestCase
from django.urls import reverse

from apps.accounts.models import Organization, User


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
