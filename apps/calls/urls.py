from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'calls', views.CallViewSet, basename='call')

urlpatterns = [
    path('', include(router.urls)),
    path('calls/sync/bulk/', views.bulk_sync_calls, name='bulk_sync_calls'),
    path('calls/statistics/', views.call_statistics, name='call_statistics'),
    path('calls/export/', views.export_calls, name='export_calls'),
    path('calls/delete-bulk/', views.delete_calls_bulk, name='delete_calls_bulk'),
    path('calls/timeline/', views.call_timeline, name='call_timeline'),
    path('calls/summary/', views.call_summary, name='call_summary'),

]
