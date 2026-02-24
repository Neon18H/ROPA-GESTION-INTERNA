from django.urls import path
from .views import StoreSettingsView

app_name = 'settings_app'
urlpatterns = [path('', StoreSettingsView.as_view(), name='index')]
