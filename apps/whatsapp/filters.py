"""
Filtros para o app whatsapp
"""
import django_filters
from django_filters import rest_framework as filters
from .models import WhatsAppMessage, WhatsAppChat


class WhatsAppMessageFilter(filters.FilterSet):
    """Filtros para o modelo WhatsAppMessage"""

    # Filtros básicos
    contact_name = filters.CharFilter(lookup_expr='icontains')
    phone_number = filters.CharFilter(lookup_expr='icontains')
    content = filters.CharFilter(lookup_expr='icontains')
    chat_id = filters.CharFilter(lookup_expr='icontains')
    whatsapp_message_id = filters.CharFilter(lookup_expr='icontains')

    # Filtros de escolha
    direction = filters.ChoiceFilter(choices=WhatsAppMessage.DIRECTION_CHOICES)
    message_type = filters.ChoiceFilter(choices=WhatsAppMessage.MESSAGE_TYPE_CHOICES)
    status = filters.ChoiceFilter(choices=WhatsAppMessage.STATUS_CHOICES)

    # Filtros de data
    message_date_after = filters.DateTimeFilter(field_name='message_date', lookup_expr='gte')
    message_date_before = filters.DateTimeFilter(field_name='message_date', lookup_expr='lte')
    synced_after = filters.DateTimeFilter(field_name='synced_at', lookup_expr='gte')
    synced_before = filters.DateTimeFilter(field_name='synced_at', lookup_expr='lte')

    # Filtros de relação
    device_id = filters.UUIDFilter(field_name='device__id')
    device_name = filters.CharFilter(field_name='device__device_name', lookup_expr='icontains')

    # Filtros booleanos
    is_group = filters.BooleanFilter()
    is_read = filters.BooleanFilter()
    is_deleted = filters.BooleanFilter()

    # Filtros de mídia
    has_media = filters.BooleanFilter(method='filter_has_media')
    media_type = filters.CharFilter(field_name='message_type', lookup_expr='in')

    def filter_has_media(self, queryset, name, value):
        if value:
            return queryset.exclude(media_url='').exclude(media_url__isnull=True)
        return queryset.filter(media_url='')

    class Meta:
        model = WhatsAppMessage
        fields = {
            'media_size': ['exact', 'gte', 'lte'],
            'media_duration': ['exact', 'gte', 'lte'],
        }


class WhatsAppChatFilter(filters.FilterSet):
    """Filtros para o modelo WhatsAppChat"""

    # Filtros básicos
    contact_name = filters.CharFilter(lookup_expr='icontains')
    phone_number = filters.CharFilter(lookup_expr='icontains')
    chat_id = filters.CharFilter(lookup_expr='icontains')
    last_message = filters.CharFilter(lookup_expr='icontains')

    # Filtros de data
    last_message_after = filters.DateTimeFilter(field_name='last_message_date', lookup_expr='gte')
    last_message_before = filters.DateTimeFilter(field_name='last_message_date', lookup_expr='lte')

    # Filtros de relação
    device_id = filters.UUIDFilter(field_name='device__id')

    # Filtros booleanos
    is_group = filters.BooleanFilter()
    is_archived = filters.BooleanFilter()
    is_muted = filters.BooleanFilter()

    # Filtros numéricos
    unread_count_min = filters.NumberFilter(field_name='unread_count', lookup_expr='gte')
    total_messages_min = filters.NumberFilter(field_name='total_messages', lookup_expr='gte')

    class Meta:
        model = WhatsAppChat
        fields = ['last_message_type']