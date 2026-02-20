"""
URLs web para o app whatsapp
"""
from django.urls import path
from apps.whatsapp import views_web

urlpatterns = [
    # Lista de mensagens
    path('whatsapp/', views_web.whatsapp_list, name='whatsapp'),

    # Lista de chats
    path('whatsapp/chats/', views_web.whatsapp_chats, name='whatsapp_chats'),

    # Estatísticas
    path('whatsapp/statistics/', views_web.whatsapp_statistics, name='whatsapp_statistics'),

    # Exportação
    path('whatsapp/export/', views_web.whatsapp_export, name='whatsapp_export'),

    # Detalhes do chat
    path('whatsapp/chat/<str:chat_id>/', views_web.whatsapp_chat_detail, name='whatsapp_chat_detail'),

    # Ações no chat
    path('whatsapp/chat/<str:chat_id>/archive/', views_web.whatsapp_archive_chat, name='whatsapp_archive_chat'),
    path('whatsapp/chat/<str:chat_id>/unarchive/', views_web.whatsapp_unarchive_chat, name='whatsapp_unarchive_chat'),
    path('whatsapp/chat/<str:chat_id>/mute/', views_web.whatsapp_mute_chat, name='whatsapp_mute_chat'),
    path('whatsapp/chat/<str:chat_id>/unmute/', views_web.whatsapp_unmute_chat, name='whatsapp_unmute_chat'),

    # Detalhes da mensagem
    path('whatsapp/message/<uuid:message_id>/', views_web.whatsapp_message_detail, name='whatsapp_message_detail'),

    # Deletar mensagem
    path('whatsapp/message/<uuid:message_id>/delete/', views_web.whatsapp_delete_message,
         name='whatsapp_delete_message'),
]