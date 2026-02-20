"""
Views para o app devices
"""
from rest_framework import viewsets, status, filters, generics
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.db.models import Q, Count
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend

from .models import Device, DeviceLog
from .serializers import DeviceSerializer, DeviceLogSerializer
from .filters import DeviceFilter, DeviceLogFilter


class DeviceViewSet(viewsets.ModelViewSet):
    """
    ViewSet para visualizar e editar dispositivos.
    """
    queryset = Device.objects.all()
    serializer_class = DeviceSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = DeviceFilter
    search_fields = ['device_name', 'device_model', 'manufacturer', 'phone_number', 'assigned_to']
    ordering_fields = ['last_sync', 'created_at', 'device_name', 'status']

    def get_queryset(self):
        """
        Filtra dispositivos pelo usuário atual.
        """
        user = self.request.user
        return Device.objects.filter(user=user)

    def perform_create(self, serializer):
        """
        Cria um novo dispositivo associado ao usuário atual.
        """
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['post'])
    def sync(self, request, pk=None):
        """
        Força uma sincronização do dispositivo.
        """
        device = self.get_object()
        device.last_sync = timezone.now()
        device.save()

        # Cria log de sincronização
        DeviceLog.objects.create(
            device=device,
            log_type='sync',
            message='Sincronização forçada pelo usuário',
            details={'user': str(request.user.id)}
        )

        return Response({
            'status': 'synced',
            'last_sync': device.last_sync
        })

    @action(detail=True, methods=['get'])
    def logs(self, request, pk=None):
        """
        Retorna os logs do dispositivo.
        """
        device = self.get_object()
        logs = device.logs.all().order_by('-created_at')[:100]
        serializer = DeviceLogSerializer(logs, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def block(self, request, pk=None):
        """
        Bloqueia o dispositivo.
        """
        device = self.get_object()
        device.status = 'blocked'
        device.save()

        DeviceLog.objects.create(
            device=device,
            log_type='warning',
            message='Dispositivo bloqueado',
            details={'reason': request.data.get('reason', '')}
        )

        return Response({'status': 'blocked'})

    @action(detail=True, methods=['post'])
    def unblock(self, request, pk=None):
        """
        Desbloqueia o dispositivo.
        """
        device = self.get_object()
        device.status = 'active'
        device.save()

        DeviceLog.objects.create(
            device=device,
            log_type='info',
            message='Dispositivo desbloqueado'
        )

        return Response({'status': 'unblocked'})

    @action(detail=True, methods=['post'])
    def update_status(self, request, pk=None):
        """
        Atualiza o status do dispositivo.
        """
        device = self.get_object()
        new_status = request.data.get('status')

        if new_status in dict(Device.STATUS_CHOICES):
            old_status = device.status
            device.status = new_status
            device.save()

            DeviceLog.objects.create(
                device=device,
                log_type='info',
                message=f'Status alterado: {old_status} -> {new_status}',
                details={'old': old_status, 'new': new_status}
            )

            return Response({'status': new_status})

        return Response(
            {'error': 'Status inválido'},
            status=status.HTTP_400_BAD_REQUEST
        )

    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """
        Retorna estatísticas dos dispositivos.
        """
        user = request.user
        devices = self.get_queryset()

        total = devices.count()
        active = devices.filter(status='active').count()
        inactive = devices.filter(status='inactive').count()
        blocked = devices.filter(status='blocked').count()

        by_os = devices.values('os_type').annotate(count=Count('id'))

        return Response({
            'total': total,
            'active': active,
            'inactive': inactive,
            'blocked': blocked,
            'by_os': by_os,
            'last_sync': devices.filter(last_sync__isnull=False).order_by('-last_sync').first()
        })


class DeviceLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet para visualizar logs de dispositivos (apenas leitura).
    """
    queryset = DeviceLog.objects.all()
    serializer_class = DeviceLogSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = DeviceLogFilter
    search_fields = ['message', 'log_type']
    ordering_fields = ['created_at', 'log_type']

    def get_queryset(self):
        """
        Filtra logs pelos dispositivos do usuário atual.
        """
        user = self.request.user
        return DeviceLog.objects.filter(device__user=user)

    @action(detail=False, methods=['get'])
    def recent(self, request):
        """
        Retorna os logs mais recentes.
        """
        logs = self.get_queryset().order_by('-created_at')[:50]
        serializer = self.get_serializer(logs, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def by_type(self, request):
        """
        Retorna logs agrupados por tipo.
        """
        logs = self.get_queryset()
        log_type = request.query_params.get('log_type')

        if log_type:
            logs = logs.filter(log_type=log_type)

        by_type = logs.values('log_type').annotate(
            count=Count('id'),
            last_date=models.Max('created_at')
        ).order_by('-count')

        return Response(by_type)


class DeviceStatisticsView(generics.RetrieveAPIView):
    """
    View para estatísticas gerais de dispositivos.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        user = request.user
        devices = Device.objects.filter(user=user)

        # Estatísticas básicas
        total_devices = devices.count()
        active_devices = devices.filter(status='active').count()

        # Últimas sincronizações
        last_syncs = devices.exclude(last_sync__isnull=True).order_by('-last_sync')[:5]
        last_sync_data = [{
            'device': d.device_name,
            'last_sync': d.last_sync
        } for d in last_syncs]

        # Logs recentes
        recent_logs = DeviceLog.objects.filter(device__user=user).order_by('-created_at')[:10]
        logs_data = DeviceLogSerializer(recent_logs, many=True).data

        return Response({
            'total_devices': total_devices,
            'active_devices': active_devices,
            'inactive_devices': total_devices - active_devices,
            'last_syncs': last_sync_data,
            'recent_logs': logs_data,
            'by_status': devices.values('status').annotate(count=Count('id')),
            'by_os': devices.values('os_type').annotate(count=Count('id')),
        })


# Funções baseadas em @api_view para ações específicas

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def bulk_device_action(request):
    """
    Executa ações em massa em múltiplos dispositivos.
    """
    device_ids = request.data.get('device_ids', [])
    action = request.data.get('action')

    if not device_ids or not action:
        return Response(
            {'error': 'device_ids e action são obrigatórios'},
            status=status.HTTP_400_BAD_REQUEST
        )

    user = request.user
    devices = Device.objects.filter(id__in=device_ids, user=user)

    if action == 'block':
        devices.update(status='blocked')
        message = f'{devices.count()} dispositivos bloqueados'
    elif action == 'unblock':
        devices.update(status='active')
        message = f'{devices.count()} dispositivos desbloqueados'
    elif action == 'delete':
        devices.delete()
        message = f'{len(device_ids)} dispositivos removidos'
    else:
        return Response(
            {'error': 'Ação inválida'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Cria logs para cada dispositivo
    for device in devices:
        DeviceLog.objects.create(
            device=device,
            log_type='info',
            message=f'Ação em massa: {action}',
            details={'bulk_action': action}
        )

    return Response({
        'success': True,
        'message': message,
        'affected': devices.count()
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def device_statistics(request):
    """
    Retorna estatísticas detalhadas dos dispositivos.
    """
    user = request.user
    devices = Device.objects.filter(user=user)

    # Estatísticas por período
    from django.db.models.functions import TruncDate
    from django.db.models import Count

    last_30_days = timezone.now() - timezone.timedelta(days=30)
    daily_syncs = devices.filter(
        last_sync__gte=last_30_days
    ).annotate(
        date=TruncDate('last_sync')
    ).values('date').annotate(
        count=Count('id')
    ).order_by('date')

    # Bateria
    battery_stats = {
        'critical': devices.filter(battery_level__lte=15).count(),
        'low': devices.filter(battery_level__gt=15, battery_level__lte=30).count(),
        'good': devices.filter(battery_level__gt=30, battery_level__lte=70).count(),
        'excellent': devices.filter(battery_level__gt=70).count(),
        'unknown': devices.filter(battery_level__isnull=True).count(),
    }

    return Response({
        'total': devices.count(),
        'by_status': devices.values('status').annotate(count=Count('id')),
        'by_os': devices.values('os_type').annotate(count=Count('id')),
        'daily_syncs': daily_syncs,
        'battery': battery_stats,
        'rooted': devices.filter(is_rooted=True).count(),
    })