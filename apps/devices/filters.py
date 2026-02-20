"""
Filtros para o app devices
"""
import django_filters
from django_filters import rest_framework as filters
from .models import Device, DeviceLog


class DeviceFilter(filters.FilterSet):
    """Filtros para o modelo Device"""

    # Filtros básicos
    device_name = filters.CharFilter(lookup_expr='icontains')
    device_model = filters.CharFilter(lookup_expr='icontains')
    manufacturer = filters.CharFilter(lookup_expr='icontains')
    phone_number = filters.CharFilter(lookup_expr='icontains')
    assigned_to = filters.CharFilter(lookup_expr='icontains')

    # Filtros de escolha
    status = filters.ChoiceFilter(choices=Device.STATUS_CHOICES)
    os_type = filters.ChoiceFilter(choices=Device.OS_CHOICES)

    # Filtros de data
    last_sync_after = filters.DateTimeFilter(field_name='last_sync', lookup_expr='gte')
    last_sync_before = filters.DateTimeFilter(field_name='last_sync', lookup_expr='lte')
    created_after = filters.DateTimeFilter(field_name='created_at', lookup_expr='gte')
    created_before = filters.DateTimeFilter(field_name='created_at', lookup_expr='lte')

    # Filtros booleanos
    is_rooted = filters.BooleanFilter()

    # Filtros de relação
    user_id = filters.NumberFilter(field_name='user__id')
    user_email = filters.CharFilter(field_name='user__email', lookup_expr='icontains')

    class Meta:
        model = Device
        fields = {
            'device_id': ['exact', 'icontains'],
            'imei': ['exact', 'icontains'],
            'app_version': ['exact', 'icontains'],
            'battery_level': ['exact', 'gte', 'lte'],
        }


class DeviceLogFilter(filters.FilterSet):
    """Filtros para o modelo DeviceLog"""

    # Filtros básicos
    log_type = filters.ChoiceFilter(choices=DeviceLog.LOG_TYPES)
    message = filters.CharFilter(lookup_expr='icontains')

    # Filtros de data
    created_after = filters.DateTimeFilter(field_name='created_at', lookup_expr='gte')
    created_before = filters.DateTimeFilter(field_name='created_at', lookup_expr='lte')

    # Filtros de relação
    device_id = filters.UUIDFilter(field_name='device__id')
    device_name = filters.CharFilter(field_name='device__device_name', lookup_expr='icontains')

    class Meta:
        model = DeviceLog
        fields = ['log_type', 'device', 'created_at']