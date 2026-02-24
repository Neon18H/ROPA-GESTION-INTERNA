from decimal import Decimal

from django.contrib import messages
from django.db import transaction
from django.db.models import Max
from django.shortcuts import get_object_or_404, redirect, render
from django.views.generic import DetailView, ListView

from apps.common.mixins import RoleRequiredMixin, role_required
from apps.inventory.models import KardexEntry
from .forms import PurchaseOrderForm
from .models import PurchaseItem, PurchaseOrder


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
                for variant_id, qty, unit_cost in rows:
                    if not variant_id:
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

    from apps.inventory.models import Variant
    variants = Variant.objects.filter(product__organization=org, is_active=True).select_related('product')[:25]
    return render(request, 'purchases/purchase_form.html', {'form': form, 'variants': variants})


class PurchaseDetailView(RoleRequiredMixin, DetailView):
    model = PurchaseOrder
    template_name = 'purchases/purchase_detail.html'
    allowed_roles = ('ADMIN', 'BODEGA')

    def get_queryset(self):
        return PurchaseOrder.objects.filter(organization=self.request.user.organization).select_related('supplier').prefetch_related('items__variant__product')


@role_required('ADMIN', 'BODEGA')
def purchase_receive_view(request, pk):
    purchase = get_object_or_404(PurchaseOrder.objects.filter(organization=request.user.organization).prefetch_related('items__variant'), pk=pk)
    if purchase.status != PurchaseOrder.Status.DRAFT:
        messages.warning(request, 'Solo se pueden recibir compras en estado borrador.')
        return redirect('purchases:detail', pk=pk)

    with transaction.atomic():
        for item in purchase.items.all():
            kardex = KardexEntry.objects.create(
                organization=purchase.organization,
                variant=item.variant,
                type=KardexEntry.Type.IN,
                qty=item.qty,
                unit_cost=item.unit_cost,
                reference=f'purchase:{purchase.id}',
                created_by=request.user,
            )
            kardex.apply_to_stock()
        purchase.status = PurchaseOrder.Status.RECEIVED
        purchase.save(update_fields=['status'])

    messages.success(request, 'Compra recibida e inventario actualizado con método de último costo.')
    return redirect('purchases:detail', pk=pk)
