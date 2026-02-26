from django.urls import path
from .views import DashboardView, RoadmapView

app_name = 'dashboard'
urlpatterns = [
    path('', DashboardView.as_view(), name='index'),
    path('roadmap/', RoadmapView.as_view(), name='roadmap'),
]
