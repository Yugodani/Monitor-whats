from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import WhatsAppMessage
from apps.devices.models import Device


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def bulk_sync_whatsapp(request):
    device_id = request.data.get('device_id')
    messages = request.data.get('messages', [])

    try:
        device = Device.objects.get(device_id=device_id, user=request.user)
    except Device.DoesNotExist:
        return Response({'error': 'Dispositivo não encontrado'}, status=404)

    created = 0
    for msg_data in messages:
        msg, created_flag = WhatsAppMessage.objects.update_or_create(
            device=device,
            phone_number=msg_data.get('phone_number', ''),
            message_date=msg_data.get('message_date'),
            defaults={
                'contact_name': msg_data.get('contact_name'),
                'content': msg_data.get('content'),
                'direction': msg_data.get('direction'),
                'is_read': msg_data.get('is_read', False),
            }
        )
        if created_flag:
            created += 1

    return Response({'created': created, 'total': len(messages)})