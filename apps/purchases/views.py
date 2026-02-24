from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.db.models import Max
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.generic import DetailView, ListView

from apps.common.mixins import RoleRequiredMixin, organization_required, role_required
from apps.inventory.models import Variant
from .forms import PurchaseOrderForm, SupplierForm
from .models import PurchaseItem, PurchaseOrder, Supplier
from .services import receive_purchase


class PurchaseListView(RoleRequiredMixin, ListView):
    model = PurchaseOrder
    template_name = 'purchases/purchase_list.html'
    allowed_roles = ('ADMIN', 'BODEGA')

    def get_queryset(self):
        org = self.get_org()
        if org is None:
            raise PermissionDenied('No organization associated to current user.')
        return PurchaseOrder.objects.filter(organization=org).select_related('supplier')


@role_required('ADMIN', 'BODEGA')
def purchase_create_view(request):
    org = request.user.organization
    if request.method == 'POST':
        form = PurchaseOrderForm(request.POST, organization=org)
        rows = list(
            zip(
                request.POST.getlist('variant_id'),
                request.POST.getlist('qty'),
                request.POST.getlist('unit_cost'),
            )
        )
        if form.is_valid() and rows:
            with transaction.atomic():
                next_number = (PurchaseOrder.objects.filter(organization=org).aggregate(m=Max('number'))['m'] or 0) + 1
                purchase = PurchaseOrder.objects.create(
                    organization=org,
                    number=next_number,
                    supplier=form.cleaned_data['supplier'],
                    created_by=request.user,
                )
                subtotal = Decimal('0')
                org_variant_ids = set(Variant.objects.filter(product__organization=org).values_list('id', flat=True))
                for variant_id, qty, unit_cost in rows:
                    if not variant_id or int(variant_id) not in org_variant_ids:
                        continue
                    line_total = Decimal(qty) * Decimal(unit_cost)
                    subtotal += line_total
                    PurchaseItem.objects.create(
                        purchase=purchase,
                        variant_id=variant_id,
                        qty=int(qty),
                        unit_cost=Decimal(unit_cost),
                        line_total=line_total,
                    )
                purchase.subtotal = subtotal
                purchase.total = subtotal
                purchase.save(update_fields=['subtotal', 'total'])
            messages.success(request, 'Orden de compra creada.')
            return redirect('purchases:detail', pk=purchase.pk)
    else:
        form = PurchaseOrderForm(organization=org)

    variants = Variant.objects.filter(product__organization=org, is_active=True).select_related('product')[:100]
    return render(request, 'purchases/order_form.html', {'form': form, 'variants': variants})


class PurchaseDetailView(RoleRequiredMixin, DetailView):
    model = PurchaseOrder
    template_name = 'purchases/order_detail.html'
    allowed_roles = ('ADMIN', 'BODEGA')

    def get_queryset(self):
        org = self.get_org()
        if org is None:
            raise PermissionDenied('No organization associated to current user.')
        return PurchaseOrder.objects.filter(organization=org).select_related('supplier').prefetch_related('items__variant__product')


@role_required('ADMIN', 'BODEGA')
def purchase_receive_view(request, pk):
    purchase = get_object_or_404(PurchaseOrder.objects.filter(organization=request.user.organization).prefetch_related('items__variant'), pk=pk)
    if purchase.status != PurchaseOrder.Status.DRAFT:
        messages.warning(request, 'Solo se pueden recibir compras en estado borrador.')
        return redirect('purchases:detail', pk=pk)

    receive_purchase(purchase, request.user)
    messages.success(request, 'Compra recibida e inventario actualizado.')
    return redirect('purchases:detail', pk=pk)


@role_required('ADMIN', 'BODEGA')
def suppliers_view(request):
    suppliers = Supplier.objects.filter(organization=request.user.organization).order_by('name')
    return render(request, 'purchases/supplier_list.html', {'suppliers': suppliers, 'form': SupplierForm()})


@login_required
@organization_required
def quick_create_supplier(request):
    if request.method == 'POST':
        form = SupplierForm(request.POST)
        if form.is_valid():
            supplier = form.save(commit=False)
            supplier.organization = request.user.organization
            supplier.save()
            return JsonResponse({'ok': True, 'id': supplier.id, 'name': supplier.name})
    return JsonResponse({'ok': False}, status=400)
