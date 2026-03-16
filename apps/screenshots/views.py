from rest_framework import viewsets, status, parsers
from rest_framework.decorators import action, permission_classes, api_view
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.utils import timezone
from datetime import datetime
from .models import Screenshot
from .serializers import ScreenshotSerializer
from apps.devices.models import Device


class ScreenshotViewSet(viewsets.ModelViewSet):
    queryset = Screenshot.objects.all()
    serializer_class = ScreenshotSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [parsers.MultiPartParser, parsers.FormParser]

    def get_queryset(self):
        return Screenshot.objects.filter(device__user=self.request.user)

    @action(detail=False, methods=['post'])
    def upload(self, request):
        """Endpoint específico para upload de screenshots"""
        device_id = request.data.get('device_id')
        image_file = request.FILES.get('image')
        timestamp = request.data.get('timestamp')

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

        screenshot = Screenshot.objects.create(
            device=device,
            image=image_file,
            timestamp=timezone.now()
        )

        serializer = self.get_serializer(screenshot, context={'request': request})
        return Response(serializer.data, status=201)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def upload_screenshot(request):
    """Versão alternativa mais simples"""
    device_id = request.data.get('device_id')
    image_file = request.FILES.get('image')

    if not all([device_id, image_file]):
        return Response({'error': 'device_id e image são obrigatórios'}, status=400)

    try:
        device = Device.objects.get(device_id=device_id, user=request.user)
    except Device.DoesNotExist:
        return Response({'error': 'Dispositivo não encontrado'}, status=404)

    screenshot = Screenshot.objects.create(
        device=device,
        image=image_file
    )

    return Response({
        'id': str(screenshot.id),
        'url': request.build_absolute_uri(screenshot.image.url),
        'timestamp': screenshot.timestamp
    }, status=201)