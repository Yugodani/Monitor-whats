"""
URLs web para o app sms_messages
"""
from django.urls import path
from apps.sms_messages import views_web

urlpatterns = [
    # Lista de mensagens
    path('messages/', views_web.message_list, name='messages'),

    # Conversas (threads)
    path('messages/threads/', views_web.message_threads, name='message_threads'),

    # Estatísticas
    path('messages/statistics/', views_web.message_statistics, name='message_statistics'),

    # Exportação
    path('messages/export/', views_web.message_export, name='message_export'),

    # Conversa com um número específico
    path('messages/conversation/<str:phone_number>/', views_web.message_conversation, name='message_conversation'),

    # Marcar conversa como lida
    path('messages/conversation/<str:phone_number>/mark-read/', views_web.message_mark_thread_read, name='message_mark_thread_read'),

    # Detalhes da mensagem
    path('messages/<uuid:message_id>/', views_web.message_detail, name='message_detail'),

    # Marcar mensagem como lida
    path('messages/<uuid:message_id>/mark-read/', views_web.message_mark_read, name='message_mark_read'),

    # Deletar mensagem
    path('messages/<uuid:message_id>/delete/', views_web.message_delete, name='message_delete'),
]
