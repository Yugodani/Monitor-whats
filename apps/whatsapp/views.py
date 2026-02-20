"""
Views para o app whatsapp
"""
from rest_framework import viewsets, status, filters, generics
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.db.models import Q, Count, Sum, Avg, Max, Min
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
import csv
import io
from datetime import datetime, timedelta

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

        # Filtros de data
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        device_id = request.query_params.get('device_id')

        if start_date:
            queryset = queryset.filter(message_date__gte=start_date)
        if end_date:
            queryset = queryset.filter(message_date__lte=end_date)
        if device_id:
            queryset = queryset.filter(device_id=device_id)

        total_messages = queryset.count()

        # Estatísticas por tipo
        by_type = queryset.values('message_type').annotate(
            count=Count('id')
        )

        # Estatísticas por direção
        by_direction = queryset.values('direction').annotate(
            count=Count('id')
        )

        # Estatísticas por status
        by_status = queryset.values('status').annotate(
            count=Count('id')
        )

        # Estatísticas por dia (últimos 30 dias)
        from django.db.models.functions import TruncDate
        last_30_days = timezone.now() - timedelta(days=30)
        by_day = queryset.filter(
            message_date__gte=last_30_days
        ).annotate(
            date=TruncDate('message_date')
        ).values('date').annotate(
            count=Count('id'),
            sent=Count('id', filter=Q(direction='sent')),
            received=Count('id', filter=Q(direction='received'))
        ).order_by('-date')

        # Contatos mais frequentes
        top_contacts = queryset.values(
            'phone_number', 'contact_name'
        ).annotate(
            count=Count('id'),
            last_message=Max('message_date')
        ).order_by('-count')[:10]

        # Estatísticas de grupos
        group_stats = {
            'total_groups': queryset.filter(is_group=True).values('chat_id').distinct().count(),
            'group_messages': queryset.filter(is_group=True).count(),
            'private_messages': queryset.filter(is_group=False).count(),
        }

        # Estatísticas de mídia
        media_stats = {
            'total_media': queryset.exclude(media_url='').count(),
            'by_media_type': queryset.exclude(media_url='').values('message_type').annotate(
                count=Count('id')
            ),
        }

        # Mensagens deletadas
        deleted_count = queryset.filter(is_deleted=True).count()

        return Response({
            'total_messages': total_messages,
            'deleted_messages': deleted_count,
            'by_type': by_type,
            'by_direction': by_direction,
            'by_status': by_status,
            'by_day': by_day,
            'top_contacts': top_contacts,
            'group_stats': group_stats,
            'media_stats': media_stats,
        })

    @action(detail=False, methods=['get'])
    def chats(self, request):
        """
        Retorna a lista de chats do WhatsApp.
        """
        user = request.user
        device_id = request.query_params.get('device_id')

        chats = WhatsAppChat.objects.filter(device__user=user)
        if device_id:
            chats = chats.filter(device_id=device_id)

        # Filtros adicionais
        is_group = request.query_params.get('is_group')
        if is_group is not None:
            chats = chats.filter(is_group=is_group.lower() == 'true')

        is_archived = request.query_params.get('is_archived')
        if is_archived is not None:
            chats = chats.filter(is_archived=is_archived.lower() == 'true')

        search = request.query_params.get('search')
        if search:
            chats = chats.filter(
                Q(contact_name__icontains=search) |
                Q(phone_number__icontains=search)
            )

        serializer = WhatsAppChatSerializer(chats, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def chat_messages(self, request):
        """
        Retorna todas as mensagens de um chat específico.
        """
        chat_id = request.query_params.get('chat_id')

        if not chat_id:
            return Response(
                {'error': 'chat_id é obrigatório'},
                status=status.HTTP_400_BAD_REQUEST
            )

        messages = self.get_queryset().filter(chat_id=chat_id)

        # Paginação
        page = self.paginate_queryset(messages)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(messages, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def mark_as_read(self, request, pk=None):
        """
        Marca uma mensagem como lida.
        """
        message = self.get_object()
        message.is_read = True
        message.status = 'read'
        message.save()

        return Response({'status': 'marked as read'})


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

    @action(detail=True, methods=['get'])
    def messages(self, request, pk=None):
        """
        Retorna as mensagens de um chat específico.
        """
        chat = self.get_object()
        messages = chat.whatsappmessage_set.all().order_by('-message_date')

        # Paginação
        page = self.paginate_queryset(messages)
        if page is not None:
            serializer = WhatsAppMessageSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = WhatsAppMessageSerializer(messages, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def archive(self, request, pk=None):
        """
        Arquiva um chat.
        """
        chat = self.get_object()
        chat.is_archived = True
        chat.save()

        return Response({'status': 'archived'})

    @action(detail=True, methods=['post'])
    def unarchive(self, request, pk=None):
        """
        Desarquiva um chat.
        """
        chat = self.get_object()
        chat.is_archived = False
        chat.save()

        return Response({'status': 'unarchived'})

    @action(detail=True, methods=['post'])
    def mute(self, request, pk=None):
        """
        Muta um chat.
        """
        chat = self.get_object()
        chat.is_muted = True
        hours = int(request.data.get('hours', 24))
        chat.mute_expiration = timezone.now() + timedelta(hours=hours)
        chat.save()

        return Response({
            'status': 'muted',
            'mute_expiration': chat.mute_expiration
        })

    @action(detail=True, methods=['post'])
    def unmute(self, request, pk=None):
        """
        Desmuta um chat.
        """
        chat = self.get_object()
        chat.is_muted = False
        chat.mute_expiration = None
        chat.save()

        return Response({'status': 'unmuted'})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def bulk_sync_whatsapp(request):
    """
    Sincroniza múltiplas mensagens e chats do WhatsApp de um dispositivo.
    """
    device_id = request.data.get('device_id')
    messages_data = request.data.get('messages', [])
    chats_data = request.data.get('chats', [])

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

    # Sincroniza chats primeiro
    chats_created = 0
    chats_updated = 0

    with transaction.atomic():
        for chat_data in chats_data:
            try:
                chat, created = WhatsAppChat.objects.update_or_create(
                    device=device,
                    chat_id=chat_data.get('chat_id'),
                    defaults={
                        'contact_name': chat_data.get('contact_name', ''),
                        'phone_number': chat_data.get('phone_number', ''),
                        'is_group': chat_data.get('is_group', False),
                        'group_name': chat_data.get('group_name', ''),
                        'last_message': chat_data.get('last_message', ''),
                        'last_message_date': chat_data.get('last_message_date'),
                        'last_message_type': chat_data.get('last_message_type', 'text'),
                        'total_messages': chat_data.get('total_messages', 0),
                        'unread_count': chat_data.get('unread_count', 0),
                        'is_archived': chat_data.get('is_archived', False),
                        'is_muted': chat_data.get('is_muted', False),
                    }
                )

                if created:
                    chats_created += 1
                else:
                    chats_updated += 1

            except Exception as e:
                print(f"Erro ao sincronizar chat: {e}")

    # Sincroniza mensagens
    messages_created = 0
    messages_updated = 0
    messages_deleted = 0
    msg_errors = []

    with transaction.atomic():
        for msg_data in messages_data:
            try:
                # Valida dados mínimos
                if not msg_data.get('whatsapp_message_id') or not msg_data.get('message_date'):
                    msg_errors.append({
                        'data': msg_data,
                        'error': 'whatsapp_message_id e message_date são obrigatórios'
                    })
                    continue

                # Verifica se é uma mensagem deletada
                if msg_data.get('is_deleted', False):
                    # Tenta encontrar a mensagem original
                    try:
                        msg = WhatsAppMessage.objects.get(
                            device=device,
                            whatsapp_message_id=msg_data['whatsapp_message_id']
                        )
                        msg.is_deleted = True
                        msg.deleted_at = timezone.now()
                        msg.original_content = msg.content
                        msg.content = "[Mensagem apagada]"
                        msg.save()
                        messages_updated += 1
                        messages_deleted += 1
                    except WhatsAppMessage.DoesNotExist:
                        # Cria como mensagem deletada
                        WhatsAppMessage.objects.create(
                            device=device,
                            whatsapp_message_id=msg_data['whatsapp_message_id'],
                            chat_id=msg_data.get('chat_id', ''),
                            contact_name=msg_data.get('contact_name', ''),
                            phone_number=msg_data.get('phone_number', ''),
                            is_group=msg_data.get('is_group', False),
                            group_name=msg_data.get('group_name', ''),
                            direction=msg_data.get('direction', 'received'),
                            message_type=msg_data.get('message_type', 'text'),
                            content="[Mensagem apagada]",
                            message_date=msg_data['message_date'],
                            is_deleted=True,
                            deleted_at=timezone.now()
                        )
                        messages_created += 1
                        messages_deleted += 1
                else:
                    # Mensagem normal
                    msg, created = WhatsAppMessage.objects.update_or_create(
                        device=device,
                        whatsapp_message_id=msg_data['whatsapp_message_id'],
                        defaults={
                            'chat_id': msg_data.get('chat_id', ''),
                            'contact_name': msg_data.get('contact_name', ''),
                            'phone_number': msg_data.get('phone_number', ''),
                            'is_group': msg_data.get('is_group', False),
                            'group_name': msg_data.get('group_name', ''),
                            'direction': msg_data.get('direction', 'received'),
                            'message_type': msg_data.get('message_type', 'text'),
                            'content': msg_data.get('content', ''),
                            'media_url': msg_data.get('media_url', ''),
                            'media_path': msg_data.get('media_path', ''),
                            'media_size': msg_data.get('media_size'),
                            'media_duration': msg_data.get('media_duration'),
                            'status': msg_data.get('status', 'sent'),
                            'is_read': msg_data.get('is_read', False),
                            'message_date': msg_data.get('message_date'),
                            'quoted_message_id': msg_data.get('quoted_message_id', ''),
                            'quoted_content': msg_data.get('quoted_content', ''),
                            'is_deleted': False,
                        }
                    )

                    if created:
                        messages_created += 1
                    else:
                        messages_updated += 1

            except Exception as e:
                msg_errors.append({
                    'data': msg_data,
                    'error': str(e)
                })

        # Atualiza última sincronização do dispositivo
        device.last_sync = timezone.now()
        device.save()

    return Response({
        'success': True,
        'device_id': device_id,
        'chats': {
            'created': chats_created,
            'updated': chats_updated,
            'total': len(chats_data)
        },
        'messages': {
            'created': messages_created,
            'updated': messages_updated,
            'deleted': messages_deleted,
            'errors': msg_errors,
            'total': len(messages_data)
        }
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def whatsapp_statistics(request):
    """
    Retorna estatísticas detalhadas das mensagens do WhatsApp.
    """
    user = request.user
    devices = Device.objects.filter(user=user)

    # Períodos
    today = timezone.now().date()
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)

    # Estatísticas por período
    stats = {}

    for period_name, start_date in [
        ('today', today),
        ('week', week_ago),
        ('month', month_ago),
        ('all', None)
    ]:
        messages = WhatsAppMessage.objects.filter(device__user=user)
        if start_date:
            messages = messages.filter(message_date__date__gte=start_date)

        stats[period_name] = {
            'total': messages.count(),
            'sent': messages.filter(direction='sent').count(),
            'received': messages.filter(direction='received').count(),
            'text': messages.filter(message_type='text').count(),
            'image': messages.filter(message_type='image').count(),
            'audio': messages.filter(message_type='audio').count(),
            'video': messages.filter(message_type='video').count(),
            'document': messages.filter(message_type='document').count(),
            'deleted': messages.filter(is_deleted=True).count(),
            'unread': messages.filter(is_read=False, direction='received').count(),
        }

    # Estatísticas de chats
    chats = WhatsAppChat.objects.filter(device__user=user)

    chat_stats = {
        'total_chats': chats.count(),
        'group_chats': chats.filter(is_group=True).count(),
        'private_chats': chats.filter(is_group=False).count(),
        'archived_chats': chats.filter(is_archived=True).count(),
        'muted_chats': chats.filter(is_muted=True).count(),
        'total_unread': chats.aggregate(Sum('unread_count'))['unread_count__sum'] or 0,
    }

    # Estatísticas por dispositivo
    by_device = []
    for device in devices:
        device_messages = WhatsAppMessage.objects.filter(device=device)
        by_device.append({
            'device_id': str(device.id),
            'device_name': device.device_name,
            'total': device_messages.count(),
            'last_message': device_messages.order_by(
                '-message_date').first().message_date if device_messages.exists() else None
        })

    # Top 10 contatos
    top_contacts = WhatsAppMessage.objects.filter(
        device__user=user
    ).values(
        'phone_number', 'contact_name'
    ).annotate(
        total=Count('id'),
        last_message=Max('message_date')
    ).order_by('-total')[:10]

    return Response({
        'periods': stats,
        'chats': chat_stats,
        'by_device': by_device,
        'top_contacts': top_contacts,
        'total_devices': devices.count(),
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def export_whatsapp(request):
    """
    Exporta mensagens do WhatsApp em formato CSV.
    """
    # Filtros
    start_date = request.query_params.get('start_date')
    end_date = request.query_params.get('end_date')
    device_id = request.query_params.get('device_id')
    chat_id = request.query_params.get('chat_id')

    messages = WhatsAppMessage.objects.filter(device__user=request.user)

    if start_date:
        messages = messages.filter(message_date__date__gte=start_date)
    if end_date:
        messages = messages.filter(message_date__date__lte=end_date)
    if device_id:
        messages = messages.filter(device_id=device_id)
    if chat_id:
        messages = messages.filter(chat_id=chat_id)

    # Ordena por data
    messages = messages.order_by('-message_date')

    # Cria arquivo CSV em memória
    output = io.StringIO()
    writer = csv.writer(output)

    # Cabeçalho
    writer.writerow([
        'Data', 'Hora', 'Tipo', 'Direção', 'Número', 'Contato',
        'Grupo', 'Conteúdo', 'Tipo Mídia', 'Status', 'Lida', 'Deletada'
    ])

    # Dados
    for msg in messages:
        writer.writerow([
            msg.message_date.strftime('%d/%m/%Y'),
            msg.message_date.strftime('%H:%M:%S'),
            'Grupo' if msg.is_group else 'Privado',
            'Enviada' if msg.direction == 'sent' else 'Recebida',
            msg.phone_number,
            msg.contact_name or '',
            msg.group_name or '',
            msg.content[:200] + ('...' if len(msg.content) > 200 else ''),
            msg.get_message_type_display(),
            msg.get_status_display(),
            'Sim' if msg.is_read else 'Não',
            'Sim' if msg.is_deleted else 'Não'
        ])

    # Prepara resposta
    response = Response(
        output.getvalue(),
        content_type='text/csv'
    )
    response['Content-Disposition'] = f'attachment; filename="whatsapp_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv"'

    return response


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def delete_whatsapp_bulk(request):
    """
    Deleta múltiplas mensagens do WhatsApp.
    """
    message_ids = request.data.get('message_ids', [])

    if not message_ids:
        return Response(
            {'error': 'message_ids é obrigatório'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Verifica se as mensagens pertencem ao usuário
    messages = WhatsAppMessage.objects.filter(
        id__in=message_ids,
        device__user=request.user
    )

    deleted_count = messages.count()

    # Soft delete (marca como deletada)
    if request.data.get('soft_delete', True):
        for msg in messages:
            msg.is_deleted = True
            msg.deleted_at = timezone.now()
            msg.original_content = msg.content
            msg.content = "[Mensagem apagada]"
            msg.save()

        message = f'{deleted_count} mensagens marcadas como deletadas'
    else:
        # Hard delete
        messages.delete()
        message = f'{deleted_count} mensagens removidas permanentemente'

    return Response({
        'success': True,
        'message': message,
        'deleted': deleted_count
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def whatsapp_timeline(request):
    """
    Retorna timeline de mensagens do WhatsApp para gráficos.
    """
    user = request.user
    days = int(request.query_params.get('days', 30))

    start_date = timezone.now() - timedelta(days=days)

    from django.db.models.functions import TruncHour, TruncDay

    # Agrupamento por hora (últimas 24h) ou dia
    if days <= 2:
        # Últimas 48h - agrupa por hora
        timeline = WhatsAppMessage.objects.filter(
            device__user=user,
            message_date__gte=start_date
        ).annotate(
            period=TruncHour('message_date')
        ).values('period').annotate(
            sent=Count('id', filter=Q(direction='sent')),
            received=Count('id', filter=Q(direction='received')),
            text=Count('id', filter=Q(message_type='text')),
            image=Count('id', filter=Q(message_type='image')),
            audio=Count('id', filter=Q(message_type='audio')),
            video=Count('id', filter=Q(message_type='video'))
        ).order_by('period')
    else:
        # Mais de 2 dias - agrupa por dia
        timeline = WhatsAppMessage.objects.filter(
            device__user=user,
            message_date__gte=start_date
        ).annotate(
            period=TruncDay('message_date')
        ).values('period').annotate(
            sent=Count('id', filter=Q(direction='sent')),
            received=Count('id', filter=Q(direction='received')),
            text=Count('id', filter=Q(message_type='text')),
            image=Count('id', filter=Q(message_type='image')),
            audio=Count('id', filter=Q(message_type='audio')),
            video=Count('id', filter=Q(message_type='video'))
        ).order_by('period')

    return Response(timeline)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def whatsapp_summary(request):
    """
    Retorna um resumo das mensagens do WhatsApp para dashboard.
    """
    user = request.user

    # Últimas 24h
    last_24h = timezone.now() - timedelta(hours=24)
    messages_24h = WhatsAppMessage.objects.filter(
        device__user=user,
        message_date__gte=last_24h
    )

    # Últimos 7 dias
    last_7d = timezone.now() - timedelta(days=7)
    messages_7d = WhatsAppMessage.objects.filter(
        device__user=user,
        message_date__gte=last_7d
    )

    # Mensagens não lidas
    unread_count = WhatsAppMessage.objects.filter(
        device__user=user,
        direction='received',
        is_read=False,
        is_deleted=False
    ).count()

    # Total de chats
    total_chats = WhatsAppChat.objects.filter(device__user=user).count()
    chats_with_unread = WhatsAppChat.objects.filter(
        device__user=user,
        unread_count__gt=0
    ).count()

    return Response({
        'last_24h': {
            'total': messages_24h.count(),
            'sent': messages_24h.filter(direction='sent').count(),
            'received': messages_24h.filter(direction='received').count(),
            'deleted': messages_24h.filter(is_deleted=True).count(),
        },
        'last_7d': {
            'total': messages_7d.count(),
            'sent': messages_7d.filter(direction='sent').count(),
            'received': messages_7d.filter(direction='received').count(),
            'deleted': messages_7d.filter(is_deleted=True).count(),
        },
        'total_all_time': WhatsAppMessage.objects.filter(device__user=user).count(),
        'unread_messages': unread_count,
        'chats': {
            'total': total_chats,
            'with_unread': chats_with_unread
        }
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def chat_messages(request, chat_id):
    """
    Retorna todas as mensagens de um chat específico (URL parameter version).
    """
    messages = WhatsAppMessage.objects.filter(
        device__user=request.user,
        chat_id=chat_id,
        is_deleted=False
    ).order_by('-message_date')

    # Paginação
    page_size = int(request.query_params.get('page_size', 50))
    page = int(request.query_params.get('page', 1))

    start = (page - 1) * page_size
    end = start + page_size

    total = messages.count()
    messages_page = messages[start:end]

    serializer = WhatsAppMessageSerializer(messages_page, many=True)

    return Response({
        'total': total,
        'page': page,
        'page_size': page_size,
        'total_pages': (total + page_size - 1) // page_size,
        'results': serializer.data
    })