from django.urls import path
from .views import SaleListView

app_name = 'sales'
urlpatterns = [path('', SaleListView.as_view(), name='list')]
