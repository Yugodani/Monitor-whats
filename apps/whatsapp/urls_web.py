from django.urls import path
from . import views_web

urlpatterns = [
    path('whatsapp/', views_web.whatsapp_list, name='whatsapp'),
    path('whatsapp/chats/', views_web.whatsapp_chats, name='whatsapp_chats'),
    path('whatsapp/statistics/', views_web.whatsapp_statistics, name='whatsapp_statistics'),
    path('whatsapp/export/', views_web.whatsapp_export, name='whatsapp_export'),
    path('whatsapp/chat/<str:chat_id>/', views_web.whatsapp_chat_detail, name='whatsapp_chat_detail'),
    path('whatsapp/chat/<str:chat_id>/archive/', views_web.whatsapp_archive_chat, name='whatsapp_archive_chat'),
    path('whatsapp/chat/<str:chat_id>/unarchive/', views_web.whatsapp_unarchive_chat, name='whatsapp_unarchive_chat'),
    path('whatsapp/chat/<str:chat_id>/mute/', views_web.whatsapp_mute_chat, name='whatsapp_mute_chat'),
    path('whatsapp/chat/<str:chat_id>/unmute/', views_web.whatsapp_unmute_chat, name='whatsapp_unmute_chat'),
    path('whatsapp/message/<uuid:message_id>/', views_web.whatsapp_message_detail, name='whatsapp_message_detail'),
    path('whatsapp/message/<uuid:message_id>/delete/', views_web.whatsapp_delete_message, name='whatsapp_delete_message'),
]