from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView
from .models import Return


class ReturnListView(LoginRequiredMixin, ListView):
    model = Return
    template_name = 'returns_app/list.html'

    def get_queryset(self):
        return Return.objects.filter(organization=self.request.user.organization)
