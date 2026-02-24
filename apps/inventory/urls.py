from django.urls import path
from .views import (
    ProductCreateView,
    ProductListView,
    ProductUpdateView,
    brands_view,
    categories_view,
    import_products,
    inventory_view,
    StockInView,
    KardexInView,
    quick_create_brand,
    quick_create_category,
)

app_name = 'inventory'
urlpatterns = [
    path('products/', ProductListView.as_view(), name='products'),
    path('products/new/', ProductCreateView.as_view(), name='product_create'),
    path('products/<int:pk>/edit/', ProductUpdateView.as_view(), name='product_update'),
    path('categories/', categories_view, name='categories'),
    path('brands/', brands_view, name='brands'),
    path('catalogs/category/quick-create/', quick_create_category, name='quick_category_create'),
    path('catalogs/brand/quick-create/', quick_create_brand, name='quick_brand_create'),
    path('', inventory_view, name='inventory'),
    path('stock-in/<int:variant_id>/', StockInView.as_view(), name='stock_in'),
    path('kardex/in/<int:variant_id>/', KardexInView.as_view(), name='kardex_in'),
    path('import/', import_products, name='import'),
]
