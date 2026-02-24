from django.urls import path
from .views import ReturnListView

app_name = 'returns'
urlpatterns = [path('', ReturnListView.as_view(), name='list')]
