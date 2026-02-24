from django.urls import path

from .views import SaleListView, SaleReceiptView, pos_view, sale_print_view

app_name = 'sales'
urlpatterns = [
    path('', SaleListView.as_view(), name='list'),
    path('pos/', pos_view, name='pos'),
    path('<int:pk>/receipt/', SaleReceiptView.as_view(), name='receipt'),
    path('<int:pk>/print/', sale_print_view, name='print'),
]
