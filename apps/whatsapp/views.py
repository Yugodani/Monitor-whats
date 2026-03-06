"""
Views para o app whatsapp (API)
"""
from rest_framework import viewsets, status, filters, generics
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db import transaction
from django.db.models import Q, Count, Sum, Avg, Max
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from datetime import timedelta

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

    @action(detail=False, methods=['get'])
    def recent(self, request):
        """Retorna as mensagens mais recentes"""
        messages = self.get_queryset().order_by('-message_date')[:50]
        serializer = self.get_serializer(messages, many=True)
        return Response(serializer.data)


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
    deleted_count = 0
    errors = []

    with transaction.atomic():
        for msg_data in messages_data:
            try:
                # Verifica se é uma mensagem deletada
                if msg_data.get('is_deleted', False):
                    # Tenta encontrar a mensagem original
                    try:
                        msg = WhatsAppMessage.objects.get(
                            device=device,
                            message_date=msg_data.get('message_date'),
                            phone_number=msg_data.get('phone_number', '')
                        )
                        msg.is_deleted = True
                        msg.deleted_at = timezone.now()
                        msg.original_content = msg.content
                        msg.content = "[Mensagem apagada]"
                        msg.save()
                        updated_count += 1
                        deleted_count += 1
                    except WhatsAppMessage.DoesNotExist:
                        # Cria como mensagem deletada
                        WhatsAppMessage.objects.create(
                            device=device,
                            phone_number=msg_data.get('phone_number', ''),
                            contact_name=msg_data.get('contact_name'),
                            direction=msg_data.get('direction', 'received'),
                            message_type=msg_data.get('message_type', 'text'),
                            content="[Mensagem apagada]",
                            message_date=msg_data.get('message_date'),
                            is_deleted=True,
                            deleted_at=timezone.now()
                        )
                        created_count += 1
                        deleted_count += 1
                else:
                    # Mensagem normal
                    msg, created = WhatsAppMessage.objects.update_or_create(
                        device=device,
                        message_date=msg_data.get('message_date'),
                        phone_number=msg_data.get('phone_number', ''),
                        defaults={
                            'contact_name': msg_data.get('contact_name'),
                            'direction': msg_data.get('direction', 'received'),
                            'message_type': msg_data.get('message_type', 'text'),
                            'content': msg_data.get('content', ''),
                            'is_read': msg_data.get('is_read', False),
                            'is_deleted': False,
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
        'deleted': deleted_count,
        'errors': errors,
        'total': len(messages_data)
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def whatsapp_statistics(request):
    """
    Retorna estatísticas detalhadas do WhatsApp.
    """
    user = request.user
    messages = WhatsAppMessage.objects.filter(device__user=user)
    chats = WhatsAppChat.objects.filter(device__user=user)

    today = timezone.now().date()
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)

    periods = {}

    for period_name, start_date in [
        ('today', today),
        ('week', week_ago),
        ('month', month_ago),
        ('all', None)
    ]:
        period_messages = messages
        if start_date:
            period_messages = messages.filter(message_date__date__gte=start_date)

        periods[period_name] = {
            'total': period_messages.count(),
            'sent': period_messages.filter(direction='sent').count(),
            'received': period_messages.filter(direction='received').count(),
            'text': period_messages.filter(message_type='text').count(),
            'image': period_messages.filter(message_type='image').count(),
            'audio': period_messages.filter(message_type='audio').count(),
            'video': period_messages.filter(message_type='video').count(),
            'document': period_messages.filter(message_type='document').count(),
            'deleted': period_messages.filter(is_deleted=True).count(),
        }

    chat_stats = {
        'total': chats.count(),
        'groups': chats.filter(is_group=True).count(),
        'private': chats.filter(is_group=False).count(),
        'archived': chats.filter(is_archived=True).count(),
        'muted': chats.filter(is_muted=True).count(),
        'total_unread': chats.aggregate(Sum('unread_count'))['unread_count__sum'] or 0,
    }

    return Response({
        'periods': periods,
        'chats': chat_stats,
    })