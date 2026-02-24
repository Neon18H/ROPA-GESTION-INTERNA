from django import forms

from .models import Brand, Category, KardexEntry, Product, Variant


class ProductForm(forms.ModelForm):
    initial_qty = forms.IntegerField(min_value=0, required=False, label='Ingreso inicial')
    initial_cost = forms.DecimalField(min_value=0, decimal_places=2, max_digits=12, required=False, label='Costo inicial')

    class Meta:
        model = Product
        fields = ['sku', 'name', 'category', 'brand', 'description', 'is_active', 'initial_qty', 'initial_cost']

    def __init__(self, *args, organization=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.organization = organization
        self.fields['category'].queryset = Category.objects.filter(organization=organization).order_by('name')
        self.fields['brand'].queryset = Brand.objects.filter(organization=organization).order_by('name')


class VariantForm(forms.ModelForm):
    class Meta:
        model = Variant
        fields = ['product', 'size', 'color', 'gender', 'barcode', 'is_active']

    def __init__(self, *args, organization=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['product'].queryset = Product.objects.filter(organization=organization).order_by('name')


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
