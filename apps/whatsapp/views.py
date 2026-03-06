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
import csv
import io

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

    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Retorna estatísticas das mensagens"""
        queryset = self.get_queryset()

        return Response({
            'total': queryset.count(),
            'sent': queryset.filter(direction='sent').count(),
            'received': queryset.filter(direction='received').count(),
            'deleted': queryset.filter(is_deleted=True).count(),
        })


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


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def export_whatsapp(request):
    """
    Exporta mensagens do WhatsApp em formato CSV.
    """
    user = request.user
    messages = WhatsAppMessage.objects.filter(
        device__user=user
    ).order_by('-message_date')

    # Criar arquivo CSV em memória
    output = io.StringIO()
    writer = csv.writer(output)

    # Cabeçalho
    writer.writerow([
        'Data',
        'Hora',
        'Contato',
        'Número',
        'Direção',
        'Tipo',
        'Conteúdo',
        'Lida',
        'Deletada'
    ])

    # Dados
    for msg in messages:
        writer.writerow([
            msg.message_date.strftime('%d/%m/%Y'),
            msg.message_date.strftime('%H:%M:%S'),
            msg.contact_name or '',
            msg.phone_number,
            'Enviada' if msg.direction == 'sent' else 'Recebida',
            msg.get_message_type_display(),
            msg.content[:200],
            'Sim' if msg.is_read else 'Não',
            'Sim' if msg.is_deleted else 'Não'
        ])

    # Prepara resposta
    response = Response(
        output.getvalue(),
        content_type='text/csv'
    )
    response['Content-Disposition'] = f'attachment; filename="whatsapp_{timezone.now().strftime("%Y%m%d_%H%M%S")}.csv"'

    return response


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_whatsapp_message(request, pk):
    """
    Deleta uma mensagem específica.
    """
    try:
        message = WhatsAppMessage.objects.get(pk=pk, device__user=request.user)
        message.delete()
        return Response({'status': 'deleted'})
    except WhatsAppMessage.DoesNotExist:
        return Response({'error': 'Mensagem não encontrada'}, status=404)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def test_whatsapp(request):
    """Endpoint de teste para verificar se está funcionando"""
    from django.utils import timezone
    from datetime import timedelta

    # Criar uma mensagem de teste
    device = Device.objects.filter(user=request.user).first()
    if device:
        msg = WhatsAppMessage.objects.create(
            device=device,
            phone_number="+5511999999999",
            contact_name="Teste",
            content="Mensagem de teste",
            message_date=timezone.now(),
            direction="received"
        )
        return Response({'status': 'ok', 'message_id': msg.id})
    return Response({'error': 'No device'}, status=400)