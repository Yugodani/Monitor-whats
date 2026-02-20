from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'messages', views.WhatsAppMessageViewSet, basename='whatsappmessage')
router.register(r'chats', views.WhatsAppChatViewSet, basename='whatsappchat')

urlpatterns = [
    path('', include(router.urls)),
    path('messages/sync/bulk/', views.bulk_sync_whatsapp, name='bulk_sync_whatsapp'),
    path('messages/export/', views.export_whatsapp, name='export_whatsapp'),
    path('messages/statistics/', views.whatsapp_statistics, name='whatsapp_statistics'),
    path('chats/<str:chat_id>/messages/', views.chat_messages, name='chat_messages'),
]