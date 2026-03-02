"""
Views web para o app sms_messages
"""
from django.db.models import Q, Count, Sum, Avg, Max
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Count, Max
from django.utils import timezone
from django.http import HttpResponse
from datetime import datetime, timedelta
import csv
import logging
logger = logging.getLogger(__name__)

from .models import SMSMessage
from apps.devices.models import Device

@login_required
def message_list(request):
    """Lista todas as mensagens do usuário"""
    user = request.user

    messages = SMSMessage.objects.filter(device__user=user)

    # Filtro para incluir/excluir mensagens deletadas
    include_deleted = request.GET.get('include_deleted', 'false').lower() == 'true'
    if not include_deleted:
        messages = messages.filter(is_deleted=False)

    # Log para debug
    print(f"Total: {messages.count()}, Incluir deletadas: {include_deleted}")

    # Filtros
    device_id = request.GET.get('device')
    direction = request.GET.get('direction')
    search = request.GET.get('search')

    if device_id:
        messages = messages.filter(device_id=device_id)

    if direction:
        messages = messages.filter(direction=direction)

    if search:
        messages = messages.filter(
            Q(phone_number__icontains=search) |
            Q(contact_name__icontains=search) |
            Q(content__icontains=search)
        )

    # Estatísticas
    total = messages.count()
    sent = messages.filter(direction='sent').count()
    received = messages.filter(direction='received').count()

    # Paginação
    paginator = Paginator(messages, 50)
    page = request.GET.get('page')
    messages_page = paginator.get_page(page)

    # Dispositivos para filtro
    devices = Device.objects.filter(user=user)

    context = {
        'messages': messages_page,
        'devices': devices,
        'total_messages': total,
        'sent_count': sent,
        'received_count': received,
        'device_filter': device_id,
        'direction_filter': direction,
        'search': search,
    }

    return render(request, 'sms_messages/list.html', context)

@login_required
def message_threads(request):
    """Lista todas as conversas"""
    user = request.user
    messages = SMSMessage.objects.filter(device__user=user, is_deleted=False)

    threads = messages.values('phone_number', 'contact_name').annotate(
        last_message_date=Max('message_date'),
        message_count=Count('id'),
        unread_count=Count('id', filter=Q(is_read=False, direction='received'))
    ).order_by('-last_message_date')

    context = {
        'threads': threads,
    }

    return render(request, 'sms_messages/threads.html', context)

@login_required
def message_detail(request, message_id):
    """Detalhes de uma mensagem"""
    message = get_object_or_404(
        SMSMessage.objects.select_related('device'),
        id=message_id,
        device__user=request.user
    )

    context = {
        'message': message,
    }

    return render(request, 'sms_messages/detail.html', context)

@login_required
def message_conversation(request, phone_number):
    """Mostra toda a conversa com um número"""
    user = request.user
    messages = SMSMessage.objects.filter(
        device__user=user,
        phone_number=phone_number,
        is_deleted=False
    ).order_by('message_date')

    # Marcar como lidas
    messages.filter(direction='received', is_read=False).update(is_read=True)

    context = {
        'messages': messages,
        'phone_number': phone_number,
    }

    return render(request, 'sms_messages/conversation.html', context)

@login_required
def message_statistics(request):
    """Estatísticas de mensagens"""
    user = request.user
    messages = SMSMessage.objects.filter(device__user=user)

    context = {
        'total': messages.count(),
        'sent': messages.filter(direction='sent').count(),
        'received': messages.filter(direction='received').count(),
        'deleted': messages.filter(is_deleted=True).count(),
        'unread': messages.filter(is_read=False, direction='received').count(),
    }

    return render(request, 'sms_messages/statistics.html', context)

@login_required
def message_export(request):
    """Exporta mensagens em CSV"""
    user = request.user
    messages = SMSMessage.objects.filter(device__user=user).order_by('-message_date')

    response = HttpResponse(content_type='text/csv')
    filename = f'mensagens_{timezone.now().strftime("%Y%m%d_%H%M%S")}.csv'
    response['Content-Disposition'] = f'attachment; filename="{filename}"'

    writer = csv.writer(response)
    writer.writerow(['Data', 'Hora', 'Tipo', 'Direção', 'Número', 'Contato', 'Conteúdo'])

    for msg in messages:
        writer.writerow([
            msg.message_date.strftime('%d/%m/%Y'),
            msg.message_date.strftime('%H:%M:%S'),
            msg.get_message_type_display(),
            'Enviada' if msg.direction == 'sent' else 'Recebida',
            msg.phone_number,
            msg.contact_name or '',
            msg.content[:100]
        ])

    return response

@login_required
def message_delete(request, message_id):
    """Marca mensagem como deletada"""
    message = get_object_or_404(SMSMessage, id=message_id, device__user=request.user)

    if request.method == 'POST':
        message.is_deleted = True
        message.deleted_at = timezone.now()
        message.save()
        messages.success(request, 'Mensagem removida com sucesso.')
        return redirect('messages')

    context = {'message': message}
    return render(request, 'sms_messages/delete.html', context)

@login_required
def message_mark_read(request, message_id):
    """Marca mensagem como lida"""
    message = get_object_or_404(SMSMessage, id=message_id, device__user=request.user)
    message.is_read = True
    message.save()
    return redirect('message_detail', message_id=message.id)

@login_required
def message_mark_thread_read(request, phone_number):
    """Marca toda a conversa como lida"""
    SMSMessage.objects.filter(
        device__user=request.user,
        phone_number=phone_number,
        direction='received',
        is_read=False
    ).update(is_read=True)

    messages.success(request, 'Conversa marcada como lida.')
    return redirect('message_conversation', phone_number=phone_number)
