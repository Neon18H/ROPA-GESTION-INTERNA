from decimal import Decimal

from django.contrib import messages
from django.db import IntegrityError, transaction
from django.db.models import Max
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views.decorators.http import require_POST
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from apps.audit.models import ActionLog
from apps.common.mixins import RoleRequiredMixin, role_required
from .forms import PurchaseItemFormSet, PurchaseOrderForm, SupplierForm
from .models import PurchaseItem, PurchaseOrder, Supplier
from .services import receive_purchase


class PurchaseListView(RoleRequiredMixin, ListView):
    model = PurchaseOrder
    template_name = 'purchases/purchase_list.html'
    allowed_roles = ('ADMIN', 'BODEGA')

    def get_queryset(self):
        return PurchaseOrder.objects.filter(organization=self.request.user.organization).select_related('supplier')


@role_required('ADMIN', 'BODEGA')
def purchase_create_view(request):
    org = request.user.organization
    if request.method == 'POST':
        form = PurchaseOrderForm(request.POST, organization=org)
        formset = PurchaseItemFormSet(request.POST, form_kwargs={'organization': org}, prefix='items')
        if form.is_valid() and formset.is_valid():
            try:
                with transaction.atomic():
                    next_number = (PurchaseOrder.objects.filter(organization=org).aggregate(m=Max('number'))['m'] or 0) + 1
                    purchase = form.save(commit=False)
                    purchase.organization = org
                    purchase.created_by = request.user
                    purchase.number = next_number
                    purchase.status = PurchaseOrder.Status.DRAFT
                    purchase.save()

                    subtotal = Decimal('0.00')
                    for item_form in formset:
                        if not item_form.cleaned_data or item_form.cleaned_data.get('DELETE'):
                            continue
                        qty = item_form.cleaned_data['qty']
                        unit_cost = item_form.cleaned_data['unit_cost']
                        variant = item_form.cleaned_data['variant']
                        line_total = Decimal(qty) * unit_cost
                        subtotal += line_total
                        PurchaseItem.objects.create(
                            purchase=purchase,
                            variant=variant,
                            qty=qty,
                            unit_cost=unit_cost,
                            line_total=line_total,
                        )

                    purchase.subtotal = subtotal
                    purchase.total = subtotal
                    purchase.save(update_fields=['subtotal', 'total'])
            except IntegrityError:
                form.add_error(None, 'No se pudo guardar la orden. Verifique los datos e intente de nuevo.')
            else:
                messages.success(request, 'Orden de compra creada.')
                return redirect('purchases:detail', pk=purchase.pk)
    else:
        form = PurchaseOrderForm(organization=org)
        formset = PurchaseItemFormSet(form_kwargs={'organization': org}, prefix='items')

    return render(request, 'purchases/order_form.html', {'form': form, 'formset': formset})


class PurchaseDetailView(RoleRequiredMixin, DetailView):
    model = PurchaseOrder
    template_name = 'purchases/order_detail.html'
    allowed_roles = ('ADMIN', 'BODEGA')

    def get_queryset(self):
        return PurchaseOrder.objects.filter(organization=self.request.user.organization).select_related('supplier').prefetch_related('items__variant__product')


@require_POST
@role_required('ADMIN', 'BODEGA')
def purchase_receive_view(request, pk):
    purchase = get_object_or_404(
        PurchaseOrder.objects.filter(organization=request.user.organization).prefetch_related('items__variant'),
        pk=pk,
    )
    if purchase.status == PurchaseOrder.Status.RECEIVED:
        messages.info(request, 'La compra ya fue recibida anteriormente.')
        return redirect('purchases:detail', pk=pk)
    if purchase.status != PurchaseOrder.Status.DRAFT:
        messages.warning(request, 'Solo se pueden recibir compras en estado borrador.')
        return redirect('purchases:detail', pk=pk)

    receive_purchase(purchase, request.user)
    ActionLog.objects.create(
        organization=request.user.organization,
        user=request.user,
        action='RECEIVE_PURCHASE',
        model='PurchaseOrder',
        object_id=str(purchase.pk),
        metadata={'status': purchase.status},
    )
    messages.success(request, 'Compra recibida e inventario actualizado.')
    return redirect('purchases:detail', pk=pk)


class SupplierQuerysetMixin(RoleRequiredMixin):
    allowed_roles = ('ADMIN', 'BODEGA')

    def get_queryset(self):
        return Supplier.objects.filter(organization=self.request.user.organization).order_by('name')


class SupplierListView(SupplierQuerysetMixin, ListView):
    model = Supplier
    template_name = 'purchases/supplier_list.html'


class SupplierCreateView(SupplierQuerysetMixin, CreateView):
    model = Supplier
    form_class = SupplierForm
    template_name = 'purchases/supplier_form.html'
    success_url = reverse_lazy('purchases:suppliers')

    def form_valid(self, form):
        form.instance.organization = self.request.user.organization
        try:
            response = super().form_valid(form)
        except IntegrityError:
            form.add_error('name', 'Ya existe un proveedor con ese nombre en tu organización.')
            return self.form_invalid(form)
        messages.success(self.request, 'Proveedor creado correctamente.')
        return response


class SupplierUpdateView(SupplierQuerysetMixin, UpdateView):
    model = Supplier
    form_class = SupplierForm
    template_name = 'purchases/supplier_form.html'
    success_url = reverse_lazy('purchases:suppliers')

    def form_valid(self, form):
        try:
            response = super().form_valid(form)
        except IntegrityError:
            form.add_error('name', 'Ya existe un proveedor con ese nombre en tu organización.')
            return self.form_invalid(form)
        messages.success(self.request, 'Proveedor actualizado correctamente.')
        return response


class SupplierDeleteView(SupplierQuerysetMixin, DeleteView):
    model = Supplier
    template_name = 'purchases/supplier_confirm_delete.html'
    success_url = reverse_lazy('purchases:suppliers')

    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Proveedor eliminado.')
        return super().delete(request, *args, **kwargs)
