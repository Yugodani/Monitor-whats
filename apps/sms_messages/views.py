"""
Views da API para o app sms_messages
"""
from rest_framework import viewsets, status, filters
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db import transaction
from django.db.models import Q, Count, Max
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend

from .models import SMSMessage
from .serializers import SMSMessageSerializer
from .filters import SMSMessageFilter
from apps.devices.models import Device

class SMSMessageViewSet(viewsets.ModelViewSet):
    queryset = SMSMessage.objects.all()
    serializer_class = SMSMessageSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = SMSMessageFilter
    search_fields = ['phone_number', 'contact_name', 'content']
    ordering_fields = ['message_date', 'created_at']

    def get_queryset(self):
        user = self.request.user
        return SMSMessage.objects.filter(device__user=user, is_deleted=False)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def bulk_sync_messages(request):
    device_id = request.data.get('device_id')
    messages_data = request.data.get('messages', [])

    try:
        device = Device.objects.get(device_id=device_id, user=request.user)
    except Device.DoesNotExist:
        return Response({'error': 'Dispositivo não encontrado'}, status=404)

    created = 0
    updated = 0

    with transaction.atomic():
        for msg_data in messages_data:
            msg, created_flag = SMSMessage.objects.update_or_create(
                device=device,
                phone_number=msg_data.get('phone_number'),
                message_date=msg_data.get('message_date'),
                defaults={
                    'content': msg_data.get('content', ''),
                    'direction': msg_data.get('direction', 'received'),
                    'is_read': msg_data.get('is_read', False),
                }
            )
            if created_flag:
                created += 1
            else:
                updated += 1

    device.last_sync = timezone.now()
    device.save()

    return Response({'created': created, 'updated': updated, 'total': len(messages_data)})
