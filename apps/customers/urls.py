from django.urls import path
from .views import CustomerListView

app_name = 'customers'
urlpatterns = [path('', CustomerListView.as_view(), name='list')]
