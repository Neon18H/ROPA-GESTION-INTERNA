from django.urls import path

from .views import SettingsBillingView, StoreSettingsView

app_name = 'settings_app'
urlpatterns = [
    path('', StoreSettingsView.as_view(), name='index'),
    path('billing/', SettingsBillingView.as_view(), name='settings_billing'),
]
