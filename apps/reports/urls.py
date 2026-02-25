from django.urls import path

from .views import (
    CustomerReportXlsxView,
    FinanceReportXlsxView,
    InventoryReportXlsxView,
    ReportsView,
)

app_name = 'reports'
urlpatterns = [
    path('', ReportsView.as_view(), name='index'),
    path('customers.xlsx', CustomerReportXlsxView.as_view(), name='customers_xlsx'),
    path('inventory.xlsx', InventoryReportXlsxView.as_view(), name='inventory_xlsx'),
    path('finance.xlsx', FinanceReportXlsxView.as_view(), name='finance_xlsx'),
]
