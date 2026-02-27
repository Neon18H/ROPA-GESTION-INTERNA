from django.test import TestCase
from django.urls import reverse

from apps.accounts.models import Organization, User


class FinanceDashboardTests(TestCase):
    def setUp(self):
        self.org = Organization.objects.create(name='Org')
        self.user = User.objects.create_user(username='fin', password='pass1234', organization=self.org, role=User.Role.ADMIN)
        self.client.force_login(self.user)

    def test_dashboard_returns_200_without_data(self):
        response = self.client.get(reverse('finance:summary'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Dashboard Financiero')

    def test_csv_exports_return_200(self):
        sales_response = self.client.get(reverse('finance:export_sales_csv'))
        purchases_response = self.client.get(reverse('finance:export_purchases_csv'))

        self.assertEqual(sales_response.status_code, 200)
        self.assertEqual(purchases_response.status_code, 200)
        self.assertIn('text/csv', sales_response['Content-Type'])
        self.assertIn('text/csv', purchases_response['Content-Type'])
