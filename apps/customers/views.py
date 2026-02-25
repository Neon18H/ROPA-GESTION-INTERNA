from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.db import IntegrityError
from django.db.models import Count, Max, Q
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import ListView, UpdateView

from apps.common.mixins import RoleRequiredMixin
from .forms import CustomerForm
from .models import Customer


class CustomerListView(RoleRequiredMixin, ListView):
    model = Customer
    template_name = 'customers/customer_list.html'
    allowed_roles = ('ADMIN', 'VENDEDOR')
    paginate_by = 20

    def get_queryset(self):
        org = self.get_org()
        if org is None:
            raise PermissionDenied('No organization associated to current user.')

        queryset = Customer.objects.filter(organization=org).annotate(total_purchases=Count('sale', distinct=True), last_purchase=Max('sale__created_at')).order_by('name')
        q = (self.request.GET.get('q') or '').strip()
        if q:
            queryset = queryset.filter(Q(name__icontains=q) | Q(email__icontains=q) | Q(phone__icontains=q))
        return queryset

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['q'] = (self.request.GET.get('q') or '').strip()
        return ctx


class CustomerUpdateView(RoleRequiredMixin, UpdateView):
    model = Customer
    form_class = CustomerForm
    template_name = 'customers/customer_form.html'
    success_url = reverse_lazy('customers:list')
    allowed_roles = ('ADMIN', 'VENDEDOR')

    def get_queryset(self):
        org = self.get_org()
        if org is None:
            raise PermissionDenied('No organization associated to current user.')
        return Customer.objects.filter(organization=org)

    def form_valid(self, form):
        try:
            self.object = form.save()
        except IntegrityError:
            form.add_error(None, 'No se pudo guardar el cliente por datos duplicados.')
            return self.form_invalid(form)

        messages.success(self.request, 'Cliente actualizado correctamente.')
        return redirect(self.get_success_url())
