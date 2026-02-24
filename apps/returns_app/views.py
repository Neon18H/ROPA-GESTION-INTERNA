from django.contrib import messages
from django.db import transaction
from django.shortcuts import redirect, render
from django.views.generic import ListView

from apps.common.mixins import RoleRequiredMixin, role_required
from apps.inventory.models import Variant
from .forms import ReturnForm
from .models import Return, ReturnItem
from .services import process_return


class ReturnListView(RoleRequiredMixin, ListView):
    model = Return
    template_name = 'returns_app/list.html'
    allowed_roles = ('ADMIN', 'VENDEDOR')

    def get_queryset(self):
        return Return.objects.filter(organization=self.request.user.organization).select_related('sale', 'created_by')


@role_required('ADMIN', 'VENDEDOR')
def return_create_view(request):
    org = request.user.organization
    if request.method == 'POST':
        form = ReturnForm(request.POST, organization=org)
        rows = zip(request.POST.getlist('variant_id'), request.POST.getlist('qty'), request.POST.getlist('action'))
        if form.is_valid():
            with transaction.atomic():
                return_order = form.save(commit=False)
                return_order.organization = org
                return_order.created_by = request.user
                return_order.save()
                org_variant_ids = set(Variant.objects.filter(product__organization=org).values_list('id', flat=True))
                for variant_id, qty, action in rows:
                    if not variant_id or int(variant_id) not in org_variant_ids:
                        continue
                    ReturnItem.objects.create(return_order=return_order, variant_id=variant_id, qty=int(qty), action=action)
                process_return(return_order, request.user)
            messages.success(request, 'Devolución registrada y stock actualizado.')
            return redirect('returns:list')
    else:
        form = ReturnForm(organization=org)

    variants = Variant.objects.filter(product__organization=org, is_active=True).select_related('product')[:100]
    return render(request, 'returns/form.html', {'form': form, 'variants': variants})
