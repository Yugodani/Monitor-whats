import django_filters
from .models import WhatsAppMessage, WhatsAppChat


class WhatsAppMessageFilter(django_filters.FilterSet):
    phone_number = django_filters.CharFilter(lookup_expr='icontains')
    contact_name = django_filters.CharFilter(lookup_expr='icontains')

    class Meta:
        model = WhatsAppMessage
        fields = ['direction', 'message_type', 'is_read', 'is_deleted']


class WhatsAppChatFilter(django_filters.FilterSet):
    contact_name = django_filters.CharFilter(lookup_expr='icontains')

    class Meta:
        model = WhatsAppChat
        fields = ['is_group', 'is_archived', 'is_muted']