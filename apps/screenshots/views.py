from rest_framework import viewsets, status, parsers
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.utils import timezone
from django.db.models import Count, Q
from datetime import timedelta
from .models import Screenshot
from .serializers import ScreenshotSerializer
from apps.devices.models import Device


class ScreenshotViewSet(viewsets.ModelViewSet):
    queryset = Screenshot.objects.all()
    serializer_class = ScreenshotSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [parsers.MultiPartParser, parsers.FormParser]

    def get_queryset(self):
        """Filtra screenshots pelo usuário atual"""
        return Screenshot.objects.filter(device__user=self.request.user)

    @action(detail=False, methods=['post'])
    def upload(self, request):
        """Endpoint específico para upload de screenshots"""
        device_id = request.data.get('device_id')
        image_file = request.FILES.get('image')
        timestamp = request.data.get('timestamp')

        # Validações
        if not device_id:
            return Response({'error': 'device_id é obrigatório'}, status=400)

        if not image_file:
            return Response({'error': 'image é obrigatório'}, status=400)

        try:
            device = Device.objects.get(device_id=device_id, user=request.user)
        except Device.DoesNotExist:
            return Response({'error': 'Dispositivo não encontrado'}, status=404)

        # Validar tipo de arquivo
        if not image_file.content_type.startswith('image/'):
            return Response({'error': 'Arquivo deve ser uma imagem'}, status=400)

        # Validar tamanho (máx 10MB)
        if image_file.size > 10 * 1024 * 1024:
            return Response({'error': 'Imagem muito grande (máx 10MB)'}, status=400)

        # Criar screenshot
        screenshot = Screenshot.objects.create(
            device=device,
            image=image_file,
            timestamp=timezone.now()
        )

        serializer = self.get_serializer(screenshot, context={'request': request})
        return Response(serializer.data, status=201)

    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Estatísticas de screenshots"""
        user = request.user
        screenshots = Screenshot.objects.filter(device__user=user)

        # Últimos 7 dias
        last_7_days = timezone.now() - timedelta(days=7)
        last_7_days_count = screenshots.filter(timestamp__gte=last_7_days).count()

        # Por dispositivo
        by_device = screenshots.values(
            'device__device_name'
        ).annotate(
            total=Count('id'),
            viewed=Count('id', filter=Q(is_viewed=True))
        ).order_by('-total')

        # Tamanho total
        total_size_mb = 0
        for s in screenshots:
            if s.file_size:
                total_size_mb += s.file_size
        total_size_mb = total_size_mb / (1024 * 1024)

        return Response({
            'total': screenshots.count(),
            'last_7_days': last_7_days_count,
            'by_device': by_device,
            'total_size_mb': round(total_size_mb, 2)
        })

    @action(detail=True, methods=['post'])
    def mark_as_viewed(self, request, pk=None):
        """Marca screenshot como visualizado"""
        screenshot = self.get_object()
        screenshot.is_viewed = True
        screenshot.save()
        return Response({'status': 'viewed'})


# ========== FUNÇÃO ADICIONAL PARA UPLOAD SIMPLES ==========
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def upload_screenshot(request):
    """
    Endpoint para upload de screenshots
    """
    print("=" * 60)
    print(f"🔵 UPLOAD RECEBIDO - {timezone.now()}")
    print(f"Usuário: {request.user.email}")

    device_id = request.data.get('device_id')
    image_file = request.FILES.get('image')
    timestamp = request.data.get('timestamp')

    if not device_id or not image_file:
        return Response(
            {'error': 'device_id e image são obrigatórios'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        device = Device.objects.get(device_id=device_id, user=request.user)
    except Device.DoesNotExist:
        return Response(
            {'error': 'Dispositivo não encontrado'},
            status=status.HTTP_404_NOT_FOUND
        )

    # Validar tipo de arquivo
    if not image_file.content_type.startswith('image/'):
        return Response(
            {'error': 'Arquivo deve ser uma imagem'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Validar tamanho
    if image_file.size > 10 * 1024 * 1024:
        return Response(
            {'error': 'Imagem muito grande (máx 10MB)'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Criar screenshot
    screenshot = Screenshot.objects.create(
        device=device,
        image=image_file,
        timestamp=timezone.now()
    )

    print(f"✅ Screenshot criado! ID: {screenshot.id}")

    return Response({
        'id': str(screenshot.id),
        'url': request.build_absolute_uri(screenshot.image.url),
        'timestamp': screenshot.timestamp,
        'file_size': screenshot.file_size
    }, status=status.HTTP_201_CREATED)
