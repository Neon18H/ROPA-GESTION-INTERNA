from django.urls import path

from .views import (
    PurchaseDetailView,
    PurchaseListView,
    purchase_create_view,
    purchase_receive_view,
    quick_create_supplier,
    suppliers_view,
)

app_name = 'purchases'
urlpatterns = [
    path('', PurchaseListView.as_view(), name='list'),
    path('new/', purchase_create_view, name='create'),
    path('suppliers/', suppliers_view, name='suppliers'),
    path('suppliers/quick-create/', quick_create_supplier, name='quick_supplier_create'),
    path('<int:pk>/', PurchaseDetailView.as_view(), name='detail'),
    path('<int:pk>/receive/', purchase_receive_view, name='receive'),
]
