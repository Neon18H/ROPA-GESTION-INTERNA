from django.test import TestCase
from django.urls import reverse

from apps.accounts.models import Organization, User


class ReportExportsTests(TestCase):
    def test_inventory_report_xlsx(self):
        org = Organization.objects.create(name='Org')
        user = User.objects.create_user(username='rep', password='pass1234', organization=org, role=User.Role.ADMIN)
        self.client.force_login(user)

        response = self.client.get(reverse('reports:inventory_xlsx'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
