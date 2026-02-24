from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView
from .models import Promotion


class PromotionListView(LoginRequiredMixin, ListView):
    model = Promotion
    template_name = 'promotions/list.html'

    def get_queryset(self):
        return Promotion.objects.filter(organization=self.request.user.organization)
