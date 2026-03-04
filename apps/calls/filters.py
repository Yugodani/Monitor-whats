"""
Filtros para o app calls
"""
import django_filters
from django_filters import rest_framework as filters
from .models import Call


class CallFilter(filters.FilterSet):
    """Filtros para o modelo Call"""

    # Filtros básicos
    phone_number = filters.CharFilter(lookup_expr='icontains')
    contact_name = filters.CharFilter(lookup_expr='icontains')

    # Filtros de escolha
    call_type = filters.ChoiceFilter(choices=Call.CALL_TYPE_CHOICES)

    # Filtros de data
    call_date_after = filters.DateTimeFilter(field_name='call_date', lookup_expr='gte')
    call_date_before = filters.DateTimeFilter(field_name='call_date', lookup_expr='lte')
    synced_after = filters.DateTimeFilter(field_name='synced_at', lookup_expr='gte')
    synced_before = filters.DateTimeFilter(field_name='synced_at', lookup_expr='lte')

    # Filtros numéricos
    duration_min = filters.NumberFilter(field_name='duration', lookup_expr='gte')
    duration_max = filters.NumberFilter(field_name='duration', lookup_expr='lte')

    # Filtros de relação
    device_id = filters.UUIDFilter(field_name='device__id')
    device_name = filters.CharFilter(field_name='device__device_name', lookup_expr='icontains')
    user_id = filters.NumberFilter(field_name='device__user__id')

    # Filtros booleanos
    is_deleted = filters.BooleanFilter()

    class Meta:
        model = Call
        # Remova os campos que não existem no modelo
        fields = []  # Vazio porque já definimos todos acima
        # OU se quiser usar o fields, use apenas os que existem:
        # fields = ['call_type', 'is_deleted']