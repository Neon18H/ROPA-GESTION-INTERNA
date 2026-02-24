from django.urls import path
from .views import PromotionListView

app_name = 'promotions'
urlpatterns = [path('', PromotionListView.as_view(), name='list')]
