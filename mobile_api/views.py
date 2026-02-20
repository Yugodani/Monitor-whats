from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from apps.devices.models import Device
from apps.devices.serializers import DeviceSerializer


@api_view(['POST'])
@permission_classes([AllowAny])
def mobile_register_device(request):
    """Register device from mobile app"""
    device_id = request.data.get('device_id')
    email = request.data.get('email')
    password = request.data.get('password')

    # Authenticate user
    user = authenticate(email=email, password=password)
    if not user:
        return Response(
            {'error': 'Invalid credentials'},
            status=status.HTTP_401_UNAUTHORIZED
        )

    # Register or update device
    device_data = {
        'device_id': device_id,
        'device_name': request.data.get('device_name', ''),
        'device_model': request.data.get('device_model', ''),
        'manufacturer': request.data.get('manufacturer', ''),
        'os_type': request.data.get('os_type', 'android'),
        'os_version': request.data.get('os_version', ''),
        'app_version': request.data.get('app_version', ''),
        'phone_number': request.data.get('phone_number', ''),
        'imei': request.data.get('imei', ''),
    }

    device, created = Device.objects.update_or_create(
        device_id=device_id,
        defaults={
            **device_data,
            'user': user,
            'status': 'active'
        }
    )

    # Generate JWT token for device
    refresh = RefreshToken.for_user(user)

    return Response({
        'success': True,
        'device': DeviceSerializer(device).data,
        'access_token': str(refresh.access_token),
        'refresh_token': str(refresh),
        'sync_interval': 300,  # Sync every 5 minutes
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mobile_sync_data(request):
    """Sync all data from mobile device"""
    device_id = request.data.get('device_id')
    data_type = request.data.get('type')  # calls, messages, whatsapp

    try:
        device = Device.objects.get(device_id=device_id, user=request.user)
    except Device.DoesNotExist:
        return Response(
            {'error': 'Device not found'},
            status=status.HTTP_404_NOT_FOUND
        )

    response_data = {'success': True, 'device_id': device_id}

    # Aqui você implementaria a lógica de sincronização para cada tipo

    return Response(response_data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def mobile_get_config(request):
    """Get device configuration"""
    device_id = request.query_params.get('device_id')

    try:
        device = Device.objects.get(device_id=device_id, user=request.user)
    except Device.DoesNotExist:
        return Response(
            {'error': 'Device not found'},
            status=status.HTTP_404_NOT_FOUND
        )

    config = {
        'sync_interval': 300,  # seconds
        'sync_on_charge_only': False,
        'sync_on_wifi_only': True,
        'max_batch_size': 1000,
        'track_calls': True,
        'track_sms': True,
        'track_whatsapp': True,
        'track_deleted_messages': True,
        'media_download': 'wifi_only',  # wifi_only, always, never
        'retention_days': 30,
    }

    return Response(config)