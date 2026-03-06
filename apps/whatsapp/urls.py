from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Criando o router
router = DefaultRouter()
router.register(r'messages', views.WhatsAppMessageViewSet, basename='whatsmessage')
router.register(r'chats', views.WhatsAppChatViewSet, basename='whatschat')

urlpatterns = [
    # Inclui as URLs do router
    path('', include(router.urls)),

    # URLs adicionais
    path('sync/bulk/', views.bulk_sync_whatsapp, name='bulk_sync_whatsapp'),
]