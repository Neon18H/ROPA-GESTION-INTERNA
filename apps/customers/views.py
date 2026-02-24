from django.core.exceptions import PermissionDenied
from django.views.generic import ListView

from apps.common.mixins import RoleRequiredMixin
from .models import Customer


class CustomerListView(RoleRequiredMixin, ListView):
    model = Customer
    template_name = 'customers/customer_list.html'
    allowed_roles = ('ADMIN', 'VENDEDOR')

    def get_queryset(self):
        org = self.get_org()
        if org is None:
            raise PermissionDenied('No organization associated to current user.')
        return Customer.objects.filter(organization=org)
