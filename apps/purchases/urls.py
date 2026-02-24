from django.urls import path
from .views import PurchaseListView

app_name = 'purchases'
urlpatterns = [path('', PurchaseListView.as_view(), name='list')]
