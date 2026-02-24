from django.contrib.auth import views as auth_views
from django.urls import path

from .views import RegisterOrganizationView, OrganizationUserListView, create_user

app_name = 'accounts'
urlpatterns = [
    path('login/', auth_views.LoginView.as_view(template_name='auth/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('register/', RegisterOrganizationView.as_view(), name='register'),
    path('users/', OrganizationUserListView.as_view(), name='user_list'),
    path('users/new/', create_user, name='user_create'),
]
