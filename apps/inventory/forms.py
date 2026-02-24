from django import forms
from django.forms import formset_factory

from .models import Brand, Category, KardexEntry, Product, Variant


class ProductForm(forms.ModelForm):
    initial_qty = forms.IntegerField(min_value=0, required=False, label='Stock inicial', initial=0)
    initial_cost = forms.DecimalField(min_value=0, decimal_places=2, max_digits=12, required=False, label='Costo inicial', help_text='Opcional para registrar Kardex de entrada inicial.')

    class Meta:
        model = Product
        fields = ['sku', 'name', 'category', 'brand', 'description', 'is_active', 'initial_qty', 'initial_cost']

    def __init__(self, *args, organization=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.organization = organization
        self.fields['category'].queryset = Category.objects.filter(organization=organization).order_by('name')
        self.fields['brand'].queryset = Brand.objects.filter(organization=organization).order_by('name')

    def clean(self):
        cleaned_data = super().clean()
        initial_qty = cleaned_data.get('initial_qty') or 0
        initial_cost = cleaned_data.get('initial_cost')

        if initial_qty == 0:
            cleaned_data['initial_cost'] = initial_cost or 0
        return cleaned_data


class VariantForm(forms.ModelForm):
    class Meta:
        model = Variant
        fields = ['product', 'size', 'color', 'gender', 'barcode', 'is_active']

    def __init__(self, *args, organization=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['product'].queryset = Product.objects.filter(organization=organization).order_by('name')


class VariantInlineForm(forms.Form):
    size = forms.CharField(max_length=16, required=False, initial='UNICA')
    color = forms.CharField(max_length=32, required=False, initial='UNICO')
    gender = forms.ChoiceField(required=False, choices=Variant.Gender.choices, initial=Variant.Gender.UNISEX)
    barcode = forms.CharField(max_length=64, required=False)

    def clean(self):
        cleaned = super().clean()
        if any(cleaned.get(field) for field in ('size', 'color', 'barcode')):
            cleaned['size'] = cleaned.get('size') or 'UNICA'
            cleaned['color'] = cleaned.get('color') or 'UNICO'
            cleaned['gender'] = cleaned.get('gender') or Variant.Gender.UNISEX
        return cleaned


VariantInlineFormSet = formset_factory(VariantInlineForm, extra=1, can_delete=True)


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name']


class BrandForm(forms.ModelForm):
    class Meta:
        model = Brand
        fields = ['name']


class StockMovementForm(forms.Form):
    variant = forms.ModelChoiceField(queryset=Variant.objects.none())
    qty = forms.IntegerField(min_value=1, label='Cantidad')
    unit_cost = forms.DecimalField(min_value=0, decimal_places=2, max_digits=12, required=False, initial=0)
    note = forms.CharField(required=False)
    movement_type = forms.ChoiceField(choices=((KardexEntry.Type.IN, 'Ingreso inicial'), (KardexEntry.Type.ADJUST, 'Ajuste')))

    def __init__(self, *args, organization=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['variant'].queryset = Variant.objects.filter(product__organization=organization, is_active=True)


class StockInForm(forms.Form):
    variant = forms.ModelChoiceField(queryset=Variant.objects.none(), widget=forms.HiddenInput)
    quantity = forms.IntegerField(min_value=1, label='Cantidad')
    unit_cost = forms.DecimalField(min_value=0, decimal_places=2, max_digits=12, required=False, label='Costo unitario')
    note = forms.CharField(required=False, widget=forms.Textarea(attrs={'rows': 2}), label='Nota')

    def __init__(self, *args, organization=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['variant'].queryset = Variant.objects.filter(product__organization=organization, is_active=True)
