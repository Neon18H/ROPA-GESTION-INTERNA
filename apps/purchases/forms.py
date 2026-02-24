from django import forms

from apps.inventory.models import Variant
from .models import PurchaseOrder, Supplier


class PurchaseOrderForm(forms.Form):
    supplier = forms.ModelChoiceField(queryset=Supplier.objects.none())

    def __init__(self, *args, organization=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['supplier'].queryset = Supplier.objects.filter(organization=organization).order_by('name')


class PurchaseItemInlineForm(forms.Form):
    variant = forms.ModelChoiceField(queryset=Variant.objects.none())
    qty = forms.IntegerField(min_value=1)
    unit_cost = forms.DecimalField(max_digits=12, decimal_places=2, min_value=0)

    def __init__(self, *args, organization=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['variant'].queryset = Variant.objects.filter(product__organization=organization, is_active=True)
