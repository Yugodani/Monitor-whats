"""
Views para o app whatsapp (API)
"""
from rest_framework import viewsets, status, filters
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db import transaction
from django.db.models import Q, Count
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend

from .models import WhatsAppMessage, WhatsAppChat
from .serializers import WhatsAppMessageSerializer, WhatsAppChatSerializer
from .filters import WhatsAppMessageFilter, WhatsAppChatFilter
from apps.devices.models import Device


# ========== VIEWSETS ==========

class WhatsAppMessageViewSet(viewsets.ModelViewSet):
    """
    ViewSet para visualizar e editar mensagens do WhatsApp.
    """
    queryset = WhatsAppMessage.objects.all()
    serializer_class = WhatsAppMessageSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = WhatsAppMessageFilter
    search_fields = ['contact_name', 'phone_number', 'content']
    ordering_fields = ['message_date', 'created_at']

    def get_queryset(self):
        user = self.request.user
        return WhatsAppMessage.objects.filter(device__user=user)


class WhatsAppChatViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet para visualizar chats do WhatsApp.
    """
    queryset = WhatsAppChat.objects.all()
    serializer_class = WhatsAppChatSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = WhatsAppChatFilter
    search_fields = ['contact_name', 'phone_number']
    ordering_fields = ['last_message_date', 'created_at']

    def get_queryset(self):
        user = self.request.user
        return WhatsAppChat.objects.filter(device__user=user)


# ========== FUNÇÕES BASEADAS EM @API_VIEW ==========

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def bulk_sync_whatsapp(request):
    """
    Sincroniza mensagens do WhatsApp de um dispositivo.
    """
    device_id = request.data.get('device_id')
    messages_data = request.data.get('messages', [])

    if not device_id:
        return Response(
            {'error': 'device_id é obrigatório'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        device = Device.objects.get(device_id=device_id, user=request.user)
    except Device.DoesNotExist:
        return Response(
            {'error': 'Dispositivo não encontrado'},
            status=status.HTTP_404_NOT_FOUND
        )

    created_count = 0

    with transaction.atomic():
        for msg_data in messages_data:
            _, created = WhatsAppMessage.objects.update_or_create(
                device=device,
                message_date=msg_data.get('message_date'),
                phone_number=msg_data.get('phone_number', ''),
                defaults={
                    'contact_name': msg_data.get('contact_name'),
                    'content': msg_data.get('content', ''),
                    'direction': msg_data.get('direction', 'received'),
                    'is_read': msg_data.get('is_read', False),
                }
            )
            if created:
                created_count += 1

    return Response({
        'success': True,
        'created': created_count,
        'total': len(messages_data)
    })