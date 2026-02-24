from django.views.generic import ListView

from apps.common.mixins import OrganizationRequiredMixin
from .models import Promotion


class PromotionListView(OrganizationRequiredMixin, ListView):
    model = Promotion
    template_name = 'promotions/list.html'

    def get_queryset(self):
        return Promotion.objects.filter(organization=self.request.user.organization)
