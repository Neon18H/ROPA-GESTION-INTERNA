from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView

from apps.common.mixins import OrganizationRequiredMixin
from .models import PurchaseOrder


class PurchaseListView(LoginRequiredMixin, OrganizationRequiredMixin, ListView):
    model = PurchaseOrder
    template_name = 'purchases/purchase_list.html'

    def get_queryset(self):
        return PurchaseOrder.objects.filter(organization=self.request.user.organization)
