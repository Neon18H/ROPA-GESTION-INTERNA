from django import forms

from apps.inventory.models import Variant
from apps.sales.models import Sale
from .models import Return, ReturnItem


class ReturnForm(forms.ModelForm):
    class Meta:
        model = Return
        fields = ['sale', 'type', 'reason']

    def __init__(self, *args, organization=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['sale'].queryset = Sale.objects.filter(organization=organization).order_by('-id')


class ReturnItemForm(forms.Form):
    variant = forms.ModelChoiceField(queryset=Variant.objects.none())
    qty = forms.IntegerField(min_value=1)
    action = forms.ChoiceField(choices=ReturnItem.Action.choices)

    def __init__(self, *args, organization=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['variant'].queryset = Variant.objects.filter(product__organization=organization, is_active=True)
