from django.urls import path
from apps.devices import views_web

urlpatterns = [
    # Lista de dispositivos
    path('devices/', views_web.device_list, name='device_list'),

    # Adicionar dispositivo
    path('devices/add/', views_web.device_add, name='device_add'),

    # Detalhes do dispositivo
    path('devices/<uuid:device_id>/', views_web.device_detail, name='device_detail'),

    # Editar dispositivo
    path('devices/<uuid:device_id>/edit/', views_web.device_edit, name='device_edit'),

    # Remover dispositivo
    path('devices/<uuid:device_id>/delete/', views_web.device_delete, name='device_delete'),

    # Logs do dispositivo
    path('devices/<uuid:device_id>/logs/', views_web.device_logs, name='device_logs'),

    # Ações no dispositivo
    path('devices/<uuid:device_id>/sync/', views_web.device_sync, name='device_sync'),
    path('devices/<uuid:device_id>/block/', views_web.device_block, name='device_block'),
    path('devices/<uuid:device_id>/unblock/', views_web.device_unblock, name='device_unblock'),
]