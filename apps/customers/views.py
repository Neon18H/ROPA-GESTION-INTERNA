from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView

from apps.common.mixins import OrganizationRequiredMixin
from .models import Customer


class CustomerListView(LoginRequiredMixin, OrganizationRequiredMixin, ListView):
    model = Customer
    template_name = 'customers/customer_list.html'

    def get_queryset(self):
        return Customer.objects.filter(organization=self.request.user.organization)
