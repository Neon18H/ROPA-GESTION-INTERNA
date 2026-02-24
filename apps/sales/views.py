from decimal import Decimal

from django.contrib import messages
from django.db import transaction
from django.db.models import Max, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.generic import DetailView, ListView

from apps.common.mixins import RoleRequiredMixin, role_required
from apps.customers.models import Customer
from apps.inventory.models import KardexEntry, Stock, Variant
from .forms import POSForm
from .models import Sale, SaleItem


class SaleListView(RoleRequiredMixin, ListView):
    model = Sale
    template_name = 'sales/sale_list.html'
    allowed_roles = ('ADMIN', 'VENDEDOR')

    def get_queryset(self):
        return Sale.objects.filter(organization=self.request.user.organization).select_related('created_by', 'customer')


@role_required('ADMIN', 'VENDEDOR')
def pos_view(request):
    org = request.user.organization
    q = request.GET.get('q', '').strip()
    variants = Variant.objects.filter(product__organization=org, is_active=True).select_related('product', 'stock')
    if q:
        variants = variants.filter(Q(product__sku__icontains=q) | Q(barcode__icontains=q) | Q(product__name__icontains=q))

    if request.method == 'POST':
        form = POSForm(request.POST, organization=org)
        items = []
        rows = zip(
            request.POST.getlist('variant_id'),
            request.POST.getlist('qty'),
            request.POST.getlist('unit_price'),
            request.POST.getlist('discount'),
        )
        for variant_id, qty, unit_price, discount in rows:
            if not variant_id:
                continue
            items.append(
                {
                    'variant': get_object_or_404(Variant, id=variant_id, product__organization=org),
                    'qty': int(qty),
                    'unit_price': Decimal(unit_price),
                    'discount': Decimal(discount or '0'),
                }
            )

        if not items:
            messages.error(request, 'Debes agregar al menos un ítem.')
        elif form.is_valid():
            allow_negative = request.user.role == 'ADMIN' and request.POST.get('allow_negative') == '1'
            for item in items:
                stock = Stock.objects.filter(variant=item['variant']).first()
                current_stock = stock.quantity if stock else 0
                if item['qty'] > current_stock and not allow_negative:
                    messages.error(request, f"Stock insuficiente para {item['variant'].product.name}.")
                    return redirect('sales:pos')

            with transaction.atomic():
                customer = form.cleaned_data['customer']
                if not customer:
                    customer = Customer.objects.create(
                        organization=org,
                        name=form.cleaned_data['customer_name'],
                        phone=form.cleaned_data['customer_phone'],
                        email=form.cleaned_data['customer_email'],
                        document_id=form.cleaned_data['customer_document_id'],
                        type=form.cleaned_data.get('customer_type') or Customer.Type.NORMAL,
                        notes=form.cleaned_data['customer_notes'],
                    )

                next_number = (Sale.objects.filter(organization=org).aggregate(m=Max('number'))['m'] or 0) + 1
                sale = Sale.objects.create(
                    organization=org,
                    number=next_number,
                    customer=customer,
                    payment_method=form.cleaned_data['payment_method'],
                    created_by=request.user,
                    status=Sale.Status.PAID,
                )

                subtotal = Decimal('0')
                discount_total = Decimal('0')
                for item in items:
                    line_total = (item['unit_price'] * item['qty']) - item['discount']
                    subtotal += item['unit_price'] * item['qty']
                    discount_total += item['discount']
                    SaleItem.objects.create(
                        sale=sale,
                        variant=item['variant'],
                        qty=item['qty'],
                        unit_price=item['unit_price'],
                        discount=item['discount'],
                        line_total=line_total,
                    )
                    kardex = KardexEntry.objects.create(
                        organization=org,
                        variant=item['variant'],
                        type=KardexEntry.Type.OUT,
                        qty=item['qty'],
                        reference=f'sale:{sale.id}',
                        created_by=request.user,
                    )
                    kardex.apply_to_stock()

                sale.subtotal = subtotal
                sale.discount_total = discount_total
                sale.total = subtotal - discount_total
                sale.save(update_fields=['subtotal', 'discount_total', 'total'])
            messages.success(request, f'Venta #{sale.number} registrada.')
            return redirect('sales:receipt', pk=sale.pk)
    else:
        form = POSForm(organization=org)

    return render(request, 'sales/pos.html', {'form': form, 'variants': variants[:20], 'query': q})


class SaleReceiptView(RoleRequiredMixin, DetailView):
    model = Sale
    template_name = 'sales/receipt.html'
    allowed_roles = ('ADMIN', 'VENDEDOR')

    def get_queryset(self):
        return Sale.objects.filter(organization=self.request.user.organization).select_related('customer').prefetch_related('items__variant__product')


@role_required('ADMIN', 'VENDEDOR')
def sale_print_view(request, pk):
    sale = get_object_or_404(
        Sale.objects.filter(organization=request.user.organization).select_related('customer').prefetch_related('items__variant__product'),
        pk=pk,
    )
    return render(request, 'sales/receipt_print.html', {'sale': sale})
