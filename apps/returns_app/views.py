from django.views.generic import ListView

from apps.common.mixins import OrganizationRequiredMixin
from .models import Return


class ReturnListView(OrganizationRequiredMixin, ListView):
    model = Return
    template_name = 'returns_app/list.html'

    def get_queryset(self):
        return Return.objects.filter(organization=self.request.user.organization)
