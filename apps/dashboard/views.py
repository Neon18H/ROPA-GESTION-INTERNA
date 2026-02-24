from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from apps.sales.models import Sale
from apps.inventory.models import Stock


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'dashboard/index.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        org = self.request.user.organization
        ctx['ventas_hoy'] = Sale.objects.filter(organization=org).count()
        ctx['ticket_promedio'] = 0
        ctx['stock_bajo'] = Stock.objects.filter(variant__product__organization=org, quantity__lte=2).count()
        return ctx
