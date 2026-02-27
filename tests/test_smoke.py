from django.test import TestCase
from django.urls import reverse

from apps.accounts.models import Organization, User


class SmokeTests(TestCase):
    def setUp(self):
        self.org = Organization.objects.create(name='Tienda Test')
        self.user = User.objects.create_user(username='admin', password='admin123', organization=self.org, role=User.Role.ADMIN)

    def test_login_page(self):
        response = self.client.get(reverse('login'))
        self.assertEqual(response.status_code, 200)

    def test_dashboard_requires_auth(self):
        response = self.client.get(reverse('dashboard:index'))
        self.assertEqual(response.status_code, 302)

    def test_dashboard_and_finance_smoke_authenticated(self):
        self.client.force_login(self.user)
        response_dashboard = self.client.get(reverse('dashboard:index'))
        response_finance = self.client.get(reverse('finance:summary'))

        self.assertEqual(response_dashboard.status_code, 200)
        self.assertEqual(response_finance.status_code, 200)
