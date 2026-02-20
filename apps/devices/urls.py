from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'devices', views.DeviceViewSet, basename='device')
router.register(r'logs', views.DeviceLogViewSet, basename='devicelog')

urlpatterns = [
    path('', include(router.urls)),
    path('devices/bulk-action/', views.bulk_device_action, name='bulk_device_action'),
    path('devices/statistics/', views.device_statistics, name='device_statistics'),
    path('devices/stats/', views.DeviceStatisticsView.as_view(), name='device_stats'),
]