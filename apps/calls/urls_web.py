from django.urls import path
from apps.calls import views_web  # Import absoluto

urlpatterns = [
    # Lista de ligações
    path('calls/', views_web.call_list, name='calls'),

    # Estatísticas
    path('calls/statistics/', views_web.call_statistics, name='call_statistics'),

    # Exportação
    path('calls/export/', views_web.call_export, name='call_export'),

    # Detalhes da ligação
    path('calls/<uuid:call_id>/', views_web.call_detail, name='call_detail'),

    # Deletar ligação
    path('calls/<uuid:call_id>/delete/', views_web.call_delete, name='call_delete'),

    # Deletar múltiplas ligações
    path('calls/delete/bulk/', views_web.call_delete_bulk, name='call_delete_bulk'),

    # Ligações por número
    path('calls/number/<str:phone_number>/', views_web.call_by_number, name='call_by_number'),

    # Timeline
    path('calls/timeline/', views_web.call_timeline, name='call_timeline'),
]