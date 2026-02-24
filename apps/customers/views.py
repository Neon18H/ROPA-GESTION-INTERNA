from django.views.generic import ListView

from apps.common.mixins import RoleRequiredMixin
from .models import Customer


class CustomerListView(RoleRequiredMixin, ListView):
    model = Customer
    template_name = 'customers/customer_list.html'
    allowed_roles = ('ADMIN', 'VENDEDOR')

    def get_queryset(self):
        return Customer.objects.filter(organization=self.request.user.organization)
