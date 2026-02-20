"""
Views para o app calls (API)
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

from .models import Call
from .serializers import CallSerializer
from .filters import CallFilter
from apps.devices.models import Device


class CallViewSet(viewsets.ModelViewSet):
    """
    ViewSet para visualizar e editar ligações.
    """
    queryset = Call.objects.all()
    serializer_class = CallSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = CallFilter
    search_fields = ['phone_number', 'contact_name', 'location']
    ordering_fields = ['call_date', 'duration', 'call_type']

    def get_queryset(self):
        """
        Filtra ligações pelos dispositivos do usuário atual.
        """
        user = self.request.user
        return Call.objects.filter(device__user=user)

    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """
        Retorna estatísticas das ligações.
        """
        queryset = self.get_queryset()

        # Filtros de data
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        device_id = request.query_params.get('device_id')

        if start_date:
            queryset = queryset.filter(call_date__gte=start_date)
        if end_date:
            queryset = queryset.filter(call_date__lte=end_date)
        if device_id:
            queryset = queryset.filter(device_id=device_id)

        total_calls = queryset.count()
        total_duration = queryset.aggregate(Sum('duration'))['duration__sum'] or 0

        # Estatísticas por tipo
        by_type = queryset.values('call_type').annotate(
            count=Count('id'),
            total_duration=Sum('duration'),
            avg_duration=Avg('duration')
        )

        # Estatísticas por dia (últimos 30 dias)
        from django.db.models.functions import TruncDate
        last_30_days = timezone.now() - timedelta(days=30)
        by_day = queryset.filter(
            call_date__gte=last_30_days
        ).annotate(
            date=TruncDate('call_date')
        ).values('date').annotate(
            count=Count('id'),
            total_duration=Sum('duration')
        ).order_by('-date')

        # Números mais chamados
        top_numbers = queryset.values(
            'phone_number', 'contact_name'
        ).annotate(
            count=Count('id'),
            total_duration=Sum('duration')
        ).order_by('-count')[:10]

        return Response({
            'total_calls': total_calls,
            'total_duration': total_duration,
            'average_duration': total_duration / total_calls if total_calls > 0 else 0,
            'by_type': by_type,
            'by_day': by_day,
            'top_numbers': top_numbers
        })

    @action(detail=False, methods=['get'])
    def recent(self, request):
        """
        Retorna as ligações mais recentes.
        """
        calls = self.get_queryset().order_by('-call_date')[:50]
        serializer = self.get_serializer(calls, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def missed(self, request):
        """
        Retorna apenas ligações perdidas.
        """
        calls = self.get_queryset().filter(call_type='missed').order_by('-call_date')[:100]
        serializer = self.get_serializer(calls, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def mark_as_deleted(self, request, pk=None):
        """
        Marca uma ligação como deletada.
        """
        call = self.get_object()
        call.is_deleted = True
        call.deleted_at = timezone.now()
        call.save()

        return Response({'status': 'marked as deleted'})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def bulk_sync_calls(request):
    """
    Sincroniza múltiplas ligações de um dispositivo.
    """
    device_id = request.data.get('device_id')
    calls_data = request.data.get('calls', [])

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
        for call_data in calls_data:
            try:
                # Valida dados mínimos
                if not call_data.get('phone_number') or not call_data.get('call_date'):
                    errors.append({
                        'data': call_data,
                        'error': 'phone_number e call_date são obrigatórios'
                    })
                    continue

                # Cria ou atualiza a ligação
                call, created = Call.objects.update_or_create(
                    device=device,
                    phone_number=call_data.get('phone_number'),
                    call_date=call_data.get('call_date'),
                    defaults={
                        'contact_name': call_data.get('contact_name', ''),
                        'call_type': call_data.get('call_type', 'missed'),
                        'duration': call_data.get('duration', 0),
                        'sim_slot': call_data.get('sim_slot'),
                        'imei': call_data.get('imei', ''),
                        'location': call_data.get('location', ''),
                        'is_deleted': call_data.get('is_deleted', False),
                    }
                )

                if created:
                    created_count += 1
                else:
                    updated_count += 1

            except Exception as e:
                errors.append({
                    'data': call_data,
                    'error': str(e)
                })

        # Atualiza última sincronização do dispositivo
        device.last_sync = timezone.now()
        device.save()

    return Response({
        'success': True,
        'device_id': device_id,
        'created': created_count,
        'updated': updated_count,
        'errors': errors,
        'total': len(calls_data)
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def call_statistics(request):
    """
    Retorna estatísticas detalhadas das ligações.
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
        calls = Call.objects.filter(device__user=user)
        if start_date:
            calls = calls.filter(call_date__date__gte=start_date)

        stats[period_name] = {
            'total': calls.count(),
            'total_duration': calls.aggregate(Sum('duration'))['duration__sum'] or 0,
            'incoming': calls.filter(call_type='incoming').count(),
            'outgoing': calls.filter(call_type='outgoing').count(),
            'missed': calls.filter(call_type='missed').count(),
            'avg_duration': calls.aggregate(Avg('duration'))['duration__avg'] or 0,
        }

    # Top 10 contatos
    top_contacts = Call.objects.filter(
        device__user=user
    ).values(
        'phone_number', 'contact_name'
    ).annotate(
        total=Count('id'),
        total_duration=Sum('duration')
    ).order_by('-total')[:10]

    return Response({
        'periods': stats,
        'top_contacts': top_contacts,
        'total_devices': devices.count(),
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def export_calls(request):
    """
    Exporta ligações em formato CSV.
    """
    # Filtros
    start_date = request.query_params.get('start_date')
    end_date = request.query_params.get('end_date')
    device_id = request.query_params.get('device_id')

    calls = Call.objects.filter(device__user=request.user)

    if start_date:
        calls = calls.filter(call_date__date__gte=start_date)
    if end_date:
        calls = calls.filter(call_date__date__lte=end_date)
    if device_id:
        calls = calls.filter(device_id=device_id)

    # Ordena por data
    calls = calls.order_by('-call_date')

    # Cria arquivo CSV em memória
    output = io.StringIO()
    writer = csv.writer(output)

    # Cabeçalho
    writer.writerow([
        'Data', 'Hora', 'Tipo', 'Número', 'Contato',
        'Duração (s)', 'Dispositivo', 'IMEI', 'Localização'
    ])

    # Dados
    for call in calls:
        writer.writerow([
            call.call_date.strftime('%d/%m/%Y'),
            call.call_date.strftime('%H:%M:%S'),
            call.get_call_type_display(),
            call.phone_number,
            call.contact_name or '',
            call.duration,
            call.device.device_name,
            call.imei or '',
            call.location or ''
        ])

    # Prepara resposta
    response = Response(
        output.getvalue(),
        content_type='text/csv'
    )
    response['Content-Disposition'] = f'attachment; filename="ligacoes_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv"'

    return response


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def delete_calls_bulk(request):
    """
    Deleta múltiplas ligações.
    """
    call_ids = request.data.get('call_ids', [])

    if not call_ids:
        return Response(
            {'error': 'call_ids é obrigatório'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Verifica se as ligações pertencem ao usuário
    calls = Call.objects.filter(
        id__in=call_ids,
        device__user=request.user
    )

    deleted_count = calls.count()

    # Soft delete (marca como deletada)
    if request.data.get('soft_delete', True):
        calls.update(
            is_deleted=True,
            deleted_at=timezone.now()
        )
        message = f'{deleted_count} ligações marcadas como deletadas'
    else:
        # Hard delete
        calls.delete()
        message = f'{deleted_count} ligações removidas permanentemente'

    return Response({
        'success': True,
        'message': message,
        'deleted': deleted_count
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def call_timeline(request):
    """
    Retorna timeline de ligações para gráficos.
    """
    user = request.user
    days = int(request.query_params.get('days', 30))

    start_date = timezone.now() - timedelta(days=days)

    from django.db.models.functions import TruncHour, TruncDay

    # Agrupamento por hora (últimas 24h) ou dia
    if days <= 2:
        # Últimas 48h - agrupa por hora
        timeline = Call.objects.filter(
            device__user=user,
            call_date__gte=start_date
        ).annotate(
            period=TruncHour('call_date')
        ).values('period').annotate(
            incoming=Count('id', filter=Q(call_type='incoming')),
            outgoing=Count('id', filter=Q(call_type='outgoing')),
            missed=Count('id', filter=Q(call_type='missed'))
        ).order_by('period')
    else:
        # Mais de 2 dias - agrupa por dia
        timeline = Call.objects.filter(
            device__user=user,
            call_date__gte=start_date
        ).annotate(
            period=TruncDay('call_date')
        ).values('period').annotate(
            incoming=Count('id', filter=Q(call_type='incoming')),
            outgoing=Count('id', filter=Q(call_type='outgoing')),
            missed=Count('id', filter=Q(call_type='missed'))
        ).order_by('period')

    return Response(timeline)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def call_summary(request):
    """
    Retorna um resumo das ligações para dashboard.
    """
    user = request.user

    # Últimas 24h
    last_24h = timezone.now() - timedelta(hours=24)
    calls_24h = Call.objects.filter(
        device__user=user,
        call_date__gte=last_24h
    )

    # Últimos 7 dias
    last_7d = timezone.now() - timedelta(days=7)
    calls_7d = Call.objects.filter(
        device__user=user,
        call_date__gte=last_7d
    )

    return Response({
        'last_24h': {
            'total': calls_24h.count(),
            'incoming': calls_24h.filter(call_type='incoming').count(),
            'outgoing': calls_24h.filter(call_type='outgoing').count(),
            'missed': calls_24h.filter(call_type='missed').count(),
            'total_duration': calls_24h.aggregate(Sum('duration'))['duration__sum'] or 0,
        },
        'last_7d': {
            'total': calls_7d.count(),
            'incoming': calls_7d.filter(call_type='incoming').count(),
            'outgoing': calls_7d.filter(call_type='outgoing').count(),
            'missed': calls_7d.filter(call_type='missed').count(),
            'total_duration': calls_7d.aggregate(Sum('duration'))['duration__sum'] or 0,
        },
        'total_all_time': Call.objects.filter(device__user=user).count(),
    })