from django.urls import path
from .views import ReturnListView, return_create_view

app_name = 'returns'
urlpatterns = [
    path('', ReturnListView.as_view(), name='list'),
    path('new/', return_create_view, name='create'),
]
