from django.urls import path

from .views import FinanceDashboardView, FinancePurchasesExportCSVView, FinanceSalesExportCSVView

app_name = 'finance'
urlpatterns = [
    path('', FinanceDashboardView.as_view(), name='summary'),
    path('dashboard/', FinanceDashboardView.as_view(), name='dashboard'),
    path('export/sales.csv', FinanceSalesExportCSVView.as_view(), name='export_sales_csv'),
    path('export/purchases.csv', FinancePurchasesExportCSVView.as_view(), name='export_purchases_csv'),
]
