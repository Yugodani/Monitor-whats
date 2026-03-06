import django_filters
from django_filters import rest_framework as filters
from .models import WhatsAppMessage, WhatsAppChat

class WhatsAppMessageFilter(filters.FilterSet):
    phone_number = filters.CharFilter(lookup_expr='icontains')
    contact_name = filters.CharFilter(lookup_expr='icontains')
    content = filters.CharFilter(lookup_expr='icontains')
    chat_id = filters.CharFilter(lookup_expr='icontains')
    direction = filters.ChoiceFilter(choices=WhatsAppMessage.DIRECTION_CHOICES)
    message_type = filters.ChoiceFilter(choices=WhatsAppMessage.MESSAGE_TYPE_CHOICES)
    message_date_after = filters.DateTimeFilter(field_name='message_date', lookup_expr='gte')
    message_date_before = filters.DateTimeFilter(field_name='message_date', lookup_expr='lte')
    is_read = filters.BooleanFilter()
    is_deleted = filters.BooleanFilter()

    class Meta:
        model = WhatsAppMessage
        fields = ['direction', 'message_type', 'is_read', 'is_deleted']

class WhatsAppChatFilter(filters.FilterSet):
    contact_name = filters.CharFilter(lookup_expr='icontains')
    phone_number = filters.CharFilter(lookup_expr='icontains')
    is_group = filters.BooleanFilter()
    is_archived = filters.BooleanFilter()
    is_muted = filters.BooleanFilter()

    class Meta:
        model = WhatsAppChat
        fields = ['is_group', 'is_archived', 'is_muted']