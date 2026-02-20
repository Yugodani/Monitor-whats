"""
URLs da API para o app sms_messages
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'messages', views.SMSMessageViewSet, basename='smsmessage')

urlpatterns = [
    path('', include(router.urls)),
    path('messages/sync/bulk/', views.bulk_sync_messages, name='bulk_sync_messages'),
]
