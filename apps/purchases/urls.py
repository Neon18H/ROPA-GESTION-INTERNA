from django.urls import path

from .views import (
    PurchaseDetailView,
    PurchaseListView,
    SupplierCreateView,
    SupplierDeleteView,
    SupplierListView,
    SupplierUpdateView,
    purchase_create_view,
    purchase_receive_view,
)

app_name = 'purchases'
urlpatterns = [
    path('', PurchaseListView.as_view(), name='list'),
    path('new/', purchase_create_view, name='create'),
    path('suppliers/', SupplierListView.as_view(), name='suppliers'),
    path('suppliers/new/', SupplierCreateView.as_view(), name='supplier_create'),
    path('suppliers/<int:pk>/edit/', SupplierUpdateView.as_view(), name='supplier_edit'),
    path('suppliers/<int:pk>/delete/', SupplierDeleteView.as_view(), name='supplier_delete'),
    path('<int:pk>/', PurchaseDetailView.as_view(), name='detail'),
    path('<int:pk>/receive/', purchase_receive_view, name='receive'),
]
