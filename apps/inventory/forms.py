from django import forms
from .models import Product, Variant


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['sku', 'name', 'category', 'brand', 'description', 'is_active']


class VariantForm(forms.ModelForm):
    class Meta:
        model = Variant
        fields = ['product', 'size', 'color', 'gender', 'barcode', 'is_active']
