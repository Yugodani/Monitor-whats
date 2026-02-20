import django_filters
from django_filters import rest_framework as filters
from .models import SMSMessage


class SMSMessageFilter(filters.FilterSet):
    phone_number = filters.CharFilter(lookup_expr='icontains')
    contact_name = filters.CharFilter(lookup_expr='icontains')
    content = filters.CharFilter(lookup_expr='icontains')
    thread_id = filters.CharFilter(lookup_expr='icontains')
    message_type = filters.ChoiceFilter(choices=SMSMessage.MESSAGE_TYPE_CHOICES)
    direction = filters.ChoiceFilter(choices=SMSMessage.DIRECTION_CHOICES)
    message_date_after = filters.DateTimeFilter(field_name='message_date', lookup_expr='gte')
    message_date_before = filters.DateTimeFilter(field_name='message_date', lookup_expr='lte')
    synced_after = filters.DateTimeFilter(field_name='synced_at', lookup_expr='gte')
    synced_before = filters.DateTimeFilter(field_name='synced_at', lookup_expr='lte')
    device_id = filters.UUIDFilter(field_name='device__id')
    device_name = filters.CharFilter(field_name='device__device_name', lookup_expr='icontains')
    is_read = filters.BooleanFilter()
    is_delivered = filters.BooleanFilter()
    is_deleted = filters.BooleanFilter()

    class Meta:
        model = SMSMessage
        fields = ['is_read', 'is_delivered', 'is_deleted']