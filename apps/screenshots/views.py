from django.shortcuts import render

from rest_framework import viewsets, status, parsers
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.utils import timezone
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
        device_id = request.data.get('device_id')
        image_file = request.FILES.get('image')

        if not device_id or not image_file:
            return Response({'error': 'Campos obrigatórios'}, status=400)

        try:
            device = Device.objects.get(device_id=device_id, user=request.user)
        except Device.DoesNotExist:
            return Response({'error': 'Dispositivo não encontrado'}, status=404)

        screenshot = Screenshot.objects.create(
            device=device,
            image=image_file
        )

        serializer = self.get_serializer(screenshot, context={'request': request})
        return Response(serializer.data, status=201)