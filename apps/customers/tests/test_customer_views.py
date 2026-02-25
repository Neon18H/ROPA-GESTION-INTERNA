from django.test import TestCase
from django.urls import reverse

from apps.accounts.models import Organization, User
from apps.customers.models import Customer


class CustomerViewsTests(TestCase):
    def setUp(self):
        self.org1 = Organization.objects.create(name='Org 1')
        self.org2 = Organization.objects.create(name='Org 2')
        self.user1 = User.objects.create_user(username='u1', password='pass1234', organization=self.org1, role=User.Role.ADMIN)
        self.user2 = User.objects.create_user(username='u2', password='pass1234', organization=self.org2, role=User.Role.ADMIN)
        self.customer = Customer.objects.create(organization=self.org1, name='Juan Perez', email='juan@example.com', phone='9999')

    def test_search_filters_customers(self):
        self.client.force_login(self.user1)

        response = self.client.get(reverse('customers:list'), {'q': 'juan'})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Juan Perez')

    def test_other_org_customer_edit_returns_404(self):
        self.client.force_login(self.user2)

        response = self.client.get(reverse('customers:edit', kwargs={'pk': self.customer.pk}))

        self.assertEqual(response.status_code, 404)

    def test_edit_customer_redirects(self):
        self.client.force_login(self.user1)

        response = self.client.post(
            reverse('customers:edit', kwargs={'pk': self.customer.pk}),
            {
                'name': 'Juan P Editado',
                'phone': '1111',
                'email': 'juan@example.com',
                'document_id': 'DOC1',
                'type': Customer.Type.NORMAL,
                'notes': 'ok',
            },
        )

        self.assertEqual(response.status_code, 302)
        self.customer.refresh_from_db()
        self.assertEqual(self.customer.name, 'Juan P Editado')
