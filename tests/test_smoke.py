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
