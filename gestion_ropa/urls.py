from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('apps.accounts.urls')),
    path('', include('apps.dashboard.urls')),
    path('inventory/', include('apps.inventory.urls')),
    path('sales/', include('apps.sales.urls')),
    path('customers/', include('apps.customers.urls')),
    path('purchases/', include('apps.purchases.urls')),
    path('finance/', include('apps.finance.urls')),
    path('reports/', include('apps.reports.urls')),
    path('promotions/', include('apps.promotions.urls')),
    path('returns/', include('apps.returns_app.urls')),
    path('settings/', include('apps.settings_app.urls')),
]
