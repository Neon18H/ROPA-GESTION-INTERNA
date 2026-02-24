from django.urls import path
from .views import RegisterOrganizationView, OrganizationUserListView, create_user

app_name = 'accounts'
urlpatterns = [
    path('register/', RegisterOrganizationView.as_view(), name='register_org'),
    path('users/', OrganizationUserListView.as_view(), name='user_list'),
    path('users/new/', create_user, name='user_create'),
]
