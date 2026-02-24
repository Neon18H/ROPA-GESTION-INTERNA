from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView
from .models import Customer


class CustomerListView(LoginRequiredMixin, ListView):
    model = Customer
    template_name = 'customers/customer_list.html'

    def get_queryset(self):
        return Customer.objects.filter(organization=self.request.user.organization)
