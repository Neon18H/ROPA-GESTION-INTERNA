from django.urls import path
from .views import ReportsView

app_name = 'reports'
urlpatterns = [path('', ReportsView.as_view(), name='index')]
