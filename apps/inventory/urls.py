from django.urls import path
from .views import (
    ProductCreateView,
    ProductListView,
    ProductUpdateView,
    catalogs_view,
    import_products,
    inventory_view,
    quick_create_brand,
    quick_create_category,
)

app_name = 'inventory'
urlpatterns = [
    path('products/', ProductListView.as_view(), name='products'),
    path('products/new/', ProductCreateView.as_view(), name='product_create'),
    path('products/<int:pk>/edit/', ProductUpdateView.as_view(), name='product_update'),
    path('catalogs/', catalogs_view, name='catalogs'),
    path('catalogs/category/quick-create/', quick_create_category, name='quick_category_create'),
    path('catalogs/brand/quick-create/', quick_create_brand, name='quick_brand_create'),
    path('', inventory_view, name='inventory'),
    path('import/', import_products, name='import'),
]
