from django.urls import path
from .views import FinanceSummaryView

app_name = 'finance'
urlpatterns = [path('', FinanceSummaryView.as_view(), name='summary')]
