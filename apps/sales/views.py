from django.views.generic import ListView

from apps.common.mixins import OrganizationRequiredMixin
from .models import Sale


class SaleListView(OrganizationRequiredMixin, ListView):
    model = Sale
    template_name = 'sales/sale_list.html'

    def get_queryset(self):
        return Sale.objects.filter(organization=self.request.user.organization).select_related('created_by', 'customer')
