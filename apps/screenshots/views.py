"""
Views para o app screenshots
"""
from rest_framework import viewsets, status, parsers
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.utils import timezone
from django.db.models import Count, Q
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from datetime import timedelta
from .models import Screenshot
from .serializers import ScreenshotSerializer
from apps.devices.models import Device
import logging

logger = logging.getLogger(__name__)


class ScreenshotViewSet(viewsets.ModelViewSet):
    """
    ViewSet para visualizar screenshots
    """
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
        return upload_screenshot(request)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def upload_screenshot(request):
    """
    Endpoint para upload de screenshots
    """
    print("=" * 60)
    print(f"🔵 UPLOAD SCREENSHOT RECEBIDO")
    print(f"Data: {timezone.now()}")
    print(f"Usuário: {request.user.email}")
    print(f"Método: {request.method}")
    print(f"Content-Type: {request.content_type}")
    print(f"FILES keys: {list(request.FILES.keys())}")
    print(f"POST keys: {list(request.POST.keys())}")

    device_id = request.data.get('device_id')
    image_file = request.FILES.get('image')
    timestamp = request.data.get('timestamp')

    print(f"device_id: {device_id}")
    print(f"type(device_id): {type(device_id)}")
    print(f"repr(device_id): {repr(device_id)}")
    print(f"image_file: {image_file.name if image_file else 'NENHUM'}")
    print(f"timestamp: {timestamp}")

    if not device_id or not image_file:
        print("❌ Campos obrigatórios faltando")
        return Response(
            {'error': 'device_id e image são obrigatórios'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # 🔍 LISTAR TODOS OS DISPOSITIVOS DO USUÁRIO
    print("\n🔍 Dispositivos do usuário:")
    devices = Device.objects.filter(user=request.user)
    print(f"Total de dispositivos: {devices.count()}")
    for d in devices:
        print(
            f"   - device_id: '{d.device_id}' | nome: {d.device_name} | status: {d.status} | last_sync: {d.last_sync}")

    try:
        # Tentar buscar o dispositivo
        device = Device.objects.get(device_id=device_id, user=request.user)
        print(f"✅ Dispositivo ENCONTRADO: {device.device_name} (ID: {device.id})")

    except Device.DoesNotExist:
        print(f"❌ Dispositivo NÃO encontrado: '{device_id}'")
        print(f"   Dica: Compare com os device_ids listados acima")
        return Response(
            {'error': 'Dispositivo não encontrado'},
            status=status.HTTP_404_NOT_FOUND
        )

    # Validar tipo de arquivo
    print(f"Content type: {image_file.content_type}")
    if not image_file.content_type.startswith('image/'):
        print(f"❌ Tipo de arquivo inválido")
        return Response(
            {'error': 'Arquivo deve ser uma imagem'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Validar tamanho
    print(f"Tamanho: {image_file.size} bytes")
    if image_file.size > 10 * 1024 * 1024:
        print(f"❌ Arquivo muito grande")
        return Response(
            {'error': 'Imagem muito grande (máx 10MB)'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Criar screenshot
    try:
        screenshot = Screenshot.objects.create(
            device=device,
            image=image_file,
            timestamp=timezone.now()
        )

        print(f"✅ Screenshot CRIADO! ID: {screenshot.id}")
        print(f"   Caminho: {screenshot.image.path}")
        print(f"   URL: {screenshot.image.url}")
        print("=" * 60)

        return Response({
            'id': str(screenshot.id),
            'url': request.build_absolute_uri(screenshot.image.url),
            'timestamp': screenshot.timestamp,
            'file_size': screenshot.file_size
        }, status=status.HTTP_201_CREATED)

    except Exception as e:
        print(f"❌ Erro ao criar screenshot: {str(e)}")
        import traceback
        traceback.print_exc()
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def debug_list_devices(request):
    """
    Endpoint para debug - lista todos os dispositivos do usuário
    """
    devices = Device.objects.filter(user=request.user).values(
        'id', 'device_id', 'device_name', 'status', 'last_sync'
    )
    return Response({
        'count': devices.count(),
        'devices': list(devices)
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def debug_list_screenshots(request):
    """
    Endpoint para debug - lista todos os screenshots do usuário
    """
    screenshots = Screenshot.objects.filter(
        device__user=request.user
    ).values('id', 'device__device_name', 'timestamp', 'image')
    return Response({
        'count': screenshots.count(),
        'screenshots': list(screenshots)
    })


# ========== VIEWS WEB ==========

@login_required
def screenshot_list(request):
    """
    Lista todos os screenshots do usuário
    """
    print("=" * 60)
    print("🔍 VIEW SCREENSHOT_LIST CHAMADA")
    print(f"Usuário: {request.user.email}")

    try:
        user = request.user
        screenshots = Screenshot.objects.filter(
            device__user=user
        ).select_related('device').order_by('-timestamp')

        print(f"📸 Total de screenshots no banco: {screenshots.count()}")

        # Listar os primeiros 5
        for s in screenshots[:5]:
            print(f"  - ID: {s.id}")
            print(f"    Device: {s.device.device_name}")
            print(f"    Timestamp: {s.timestamp}")
            if s.image:
                print(f"    Image URL: {s.image.url}")
                print(f"    Image path: {s.image.path}")
            else:
                print(f"    Image: SEM IMAGEM")

        paginator = Paginator(screenshots, 24)
        page = request.GET.get('page', 1)
        screenshots_page = paginator.get_page(page)

        context = {
            'screenshots': screenshots_page,
            'total': screenshots.count(),
        }

        print("✅ Renderizando template")
        return render(request, 'screenshots/list.html', context)

    except Exception as e:
        print(f"❌ ERRO: {str(e)}")
        import traceback
        traceback.print_exc()

        return render(request, 'screenshots/list.html', {
            'error': str(e),
            'screenshots': [],
            'total': 0
        })