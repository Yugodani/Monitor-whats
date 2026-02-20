from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.mobile_register_device, name='mobile_register'),
    path('sync/', views.mobile_sync_data, name='mobile_sync'),
    path('config/', views.mobile_get_config, name='mobile_config'),
    ]