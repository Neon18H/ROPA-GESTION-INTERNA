from django.urls import path

from .views import FinanceDashboardView

app_name = 'finance'
urlpatterns = [
    path('', FinanceDashboardView.as_view(), name='summary'),
    path('dashboard/', FinanceDashboardView.as_view(), name='dashboard'),
]
