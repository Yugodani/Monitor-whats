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


class WhatsAppMessageViewSet(viewsets.ModelViewSet):
    """
    ViewSet para visualizar e editar mensagens do WhatsApp.
    """
    queryset = WhatsAppMessage.objects.all()
    serializer_class = WhatsAppMessageSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = WhatsAppMessageFilter
    search_fields = ['contact_name', 'phone_number', 'content', 'group_name']
    ordering_fields = ['message_date', 'created_at']

    def get_queryset(self):
        """
        Filtra mensagens pelos dispositivos do usuário atual.
        """
        user = self.request.user
        queryset = WhatsAppMessage.objects.filter(device__user=user)

        # Filtro para incluir/excluir mensagens deletadas
        include_deleted = self.request.query_params.get('include_deleted', 'false').lower() == 'true'
        if not include_deleted:
            queryset = queryset.filter(is_deleted=False)

        return queryset

    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """
        Retorna estatísticas das mensagens do WhatsApp.
        """
        queryset = self.get_queryset()

        total_messages = queryset.count()
        deleted_messages = queryset.filter(is_deleted=True).count()

        # Estatísticas por tipo
        by_type = queryset.values('message_type').annotate(count=Count('id'))

        # Estatísticas por direção
        by_direction = queryset.values('direction').annotate(count=Count('id'))

        return Response({
            'total_messages': total_messages,
            'deleted_messages': deleted_messages,
            'by_type': by_type,
            'by_direction': by_direction,
        })


class WhatsAppChatViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet para visualizar chats do WhatsApp (apenas leitura).
    """
    queryset = WhatsAppChat.objects.all()
    serializer_class = WhatsAppChatSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = WhatsAppChatFilter
    search_fields = ['contact_name', 'phone_number', 'group_name']
    ordering_fields = ['last_message_date', 'created_at']

    def get_queryset(self):
        """
        Filtra chats pelos dispositivos do usuário atual.
        """
        user = self.request.user
        return WhatsAppChat.objects.filter(device__user=user)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def bulk_sync_whatsapp(request):
    """
    Sincroniza múltiplas mensagens do WhatsApp de um dispositivo.
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
    updated_count = 0
    errors = []

    with transaction.atomic():
        for msg_data in messages_data:
            try:
                msg, created = WhatsAppMessage.objects.update_or_create(
                    device=device,
                    phone_number=msg_data.get('phone_number', ''),
                    message_date=msg_data.get('message_date'),
                    defaults={
                        'contact_name': msg_data.get('contact_name'),
                        'content': msg_data.get('content', ''),
                        'direction': msg_data.get('direction', 'received'),
                        'is_read': msg_data.get('is_read', False),
                        'is_deleted': msg_data.get('is_deleted', False),
                    }
                )

                if created:
                    created_count += 1
                else:
                    updated_count += 1

            except Exception as e:
                errors.append({
                    'data': msg_data,
                    'error': str(e)
                })

    return Response({
        'success': True,
        'created': created_count,
        'updated': updated_count,
        'errors': errors,
        'total': len(messages_data)
    })