from django.test import TestCase
from django.urls import reverse

from apps.accounts.models import Organization, User


class FinanceDashboardTests(TestCase):
    def test_dashboard_returns_200(self):
        org = Organization.objects.create(name='Org')
        user = User.objects.create_user(username='fin', password='pass1234', organization=org, role=User.Role.ADMIN)
        self.client.force_login(user)

        response = self.client.get(reverse('finance:summary'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Inventario valorizado')
