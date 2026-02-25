from django.urls import path

from .views import CustomerListView, CustomerUpdateView

app_name = 'customers'
urlpatterns = [
    path('', CustomerListView.as_view(), name='list'),
    path('<int:pk>/edit/', CustomerUpdateView.as_view(), name='edit'),
]
