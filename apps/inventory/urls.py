from django.urls import path
from .views import ProductListView, ProductCreateView, inventory_view, import_products

app_name = 'inventory'
urlpatterns = [
    path('products/', ProductListView.as_view(), name='products'),
    path('products/new/', ProductCreateView.as_view(), name='product_create'),
    path('', inventory_view, name='inventory'),
    path('import/', import_products, name='import'),
]
