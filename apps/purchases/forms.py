from django import forms
from django.forms import BaseFormSet, formset_factory

from apps.inventory.models import Variant
from .models import PurchaseOrder, Supplier


class SupplierForm(forms.ModelForm):
    class Meta:
        model = Supplier
        fields = ['name', 'phone', 'email', 'address', 'notes', 'is_active']


class PurchaseOrderForm(forms.ModelForm):
    class Meta:
        model = PurchaseOrder
        fields = ['supplier', 'notes']

    def __init__(self, *args, organization=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['supplier'].queryset = Supplier.objects.filter(organization=organization, is_active=True).order_by('name')


class PurchaseItemForm(forms.Form):
    variant = forms.ModelChoiceField(queryset=Variant.objects.none())
    qty = forms.IntegerField(min_value=1)
    unit_cost = forms.DecimalField(max_digits=12, decimal_places=2, min_value=0)

    def __init__(self, *args, organization=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['variant'].queryset = Variant.objects.filter(product__organization=organization, is_active=True).select_related('product')


class BasePurchaseItemFormSet(BaseFormSet):
    def clean(self):
        super().clean()
        has_rows = False
        for form in self.forms:
            if not hasattr(form, 'cleaned_data'):
                continue
            if form.cleaned_data and not form.cleaned_data.get('DELETE', False):
                has_rows = True
        if not has_rows:
            raise forms.ValidationError('Debe agregar al menos un ítem en la compra.')


PurchaseItemFormSet = formset_factory(PurchaseItemForm, formset=BasePurchaseItemFormSet, extra=1, can_delete=True)
