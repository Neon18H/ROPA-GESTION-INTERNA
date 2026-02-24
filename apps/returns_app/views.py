from django.views.generic import ListView

from apps.common.mixins import RoleRequiredMixin
from .models import Return


class ReturnListView(RoleRequiredMixin, ListView):
    model = Return
    template_name = 'returns_app/list.html'
    allowed_roles = ('ADMIN', 'VENDEDOR')

    def get_queryset(self):
        return Return.objects.filter(organization=self.request.user.organization)
