from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'messages', views.WhatsAppMessageViewSet, basename='whatsmessage')
router.register(r'chats', views.WhatsAppChatViewSet, basename='whatschat')

urlpatterns = [
    path('', include(router.urls)),
    path('sync/bulk/', views.bulk_sync_whatsapp, name='bulk_sync_whatsapp'),
    path('statistics/', views.whatsapp_statistics, name='whatsapp_statistics'),
    path('export/', views.export_whatsapp, name='export_whatsapp'),
    path('message/<uuid:pk>/', views.delete_whatsapp_message, name='delete_whatsapp_message'),
]