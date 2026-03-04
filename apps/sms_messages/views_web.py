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
    user = request.user

    # Buscar mensagens
    messages = SMSMessage.objects.filter(
        device__user=user,
        is_deleted=False
    ).select_related('device').order_by('-message_date')[:50]

    # Verificar se as mensagens têm os campos esperados
    if messages.exists():
        primeira = messages.first()

    context = {
        'sms_messages': messages,  # ← NOME CORRETO
        'total_messages': messages.count(),
        # ... outros campos
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
        'sms_messages': messages,
        'phone_number': phone_number,
    }

    return render(request, 'sms_messages/conversation.html', context)


@login_required
def message_statistics(request):
    """
    Estatísticas detalhadas de mensagens
    """
    user = request.user
    messages = SMSMessage.objects.filter(device__user=user)

    # Períodos para análise
    today = timezone.now().date()
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)

    # Estatísticas por período
    periods = {}

    for period_name, start_date in [
        ('today', today),
        ('week', week_ago),
        ('month', month_ago),
        ('all', None)
    ]:
        period_messages = messages
        if start_date:
            period_messages = messages.filter(message_date__date__gte=start_date)

        periods[period_name] = {
            'total': period_messages.count(),
            'sent': period_messages.filter(direction='sent').count(),
            'received': period_messages.filter(direction='received').count(),
            'sms': period_messages.filter(message_type='sms').count(),
            'mms': period_messages.filter(message_type='mms').count(),
            'deleted': period_messages.filter(is_deleted=True).count(),
            'unread': period_messages.filter(is_read=False, direction='received').count(),
        }

    # Estatísticas por dispositivo
    devices = Device.objects.filter(user=user)
    device_stats = []

    for device in devices:
        device_messages = messages.filter(device=device)
        device_stats.append({
            'device': device,
            'total': device_messages.count(),
            'sent': device_messages.filter(direction='sent').count(),
            'received': device_messages.filter(direction='received').count(),
            'last_message': device_messages.order_by(
                '-message_date').first().message_date if device_messages.exists() else None,
        })

    # Top 10 contatos
    top_contacts = messages.values(
        'phone_number', 'contact_name'
    ).annotate(
        total=Count('id'),
        last_message=Max('message_date')
    ).order_by('-total')[:10]

    # Dados para gráfico dos últimos 30 dias
    from django.db.models.functions import TruncDate

    last_30_days = timezone.now() - timedelta(days=30)
    daily_stats = messages.filter(
        message_date__gte=last_30_days
    ).annotate(
        date=TruncDate('message_date')
    ).values('date').annotate(
        total=Count('id'),
        sent=Count('id', filter=Q(direction='sent')),
        received=Count('id', filter=Q(direction='received'))
    ).order_by('date')

    # Preparar dados para o gráfico
    chart_labels = []
    chart_sent = []
    chart_received = []

    for day in daily_stats:
        chart_labels.append(day['date'].strftime('%d/%m'))
        chart_sent.append(day['sent'])
        chart_received.append(day['received'])

    context = {
        'periods': periods,
        'device_stats': device_stats,
        'top_contacts': top_contacts,
        'chart_labels': chart_labels,
        'chart_sent': chart_sent,
        'chart_received': chart_received,
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
