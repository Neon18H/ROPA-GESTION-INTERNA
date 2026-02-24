from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView

from apps.common.mixins import OrganizationRequiredMixin
from .models import Sale


class SaleListView(LoginRequiredMixin, OrganizationRequiredMixin, ListView):
    model = Sale
    template_name = 'sales/sale_list.html'

    def get_queryset(self):
        return Sale.objects.filter(organization=self.request.user.organization).select_related('created_by', 'customer')
