"""
Views web para o app whatsapp - Interface de usuário para mensagens WhatsApp
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

from .models import WhatsAppMessage, WhatsAppChat
from apps.devices.models import Device


@login_required
def whatsapp_list(request):
    """
    Lista todas as mensagens do WhatsApp do usuário
    """
    user = request.user

    # Busca todas as mensagens dos dispositivos do usuário
    messages = WhatsAppMessage.objects.filter(
        device__user=user,
        is_deleted=False
    ).select_related('device').order_by('-message_date')

    # Filtros
    device_id = request.GET.get('device')
    chat_id = request.GET.get('chat')
    direction = request.GET.get('direction')
    message_type = request.GET.get('type')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    search = request.GET.get('search')

    if device_id:
        messages = messages.filter(device_id=device_id)

    if chat_id:
        messages = messages.filter(chat_id=chat_id)

    if direction:
        messages = messages.filter(direction=direction)

    if message_type:
        messages = messages.filter(message_type=message_type)

    if start_date:
        messages = messages.filter(message_date__date__gte=start_date)

    if end_date:
        messages = messages.filter(message_date__date__lte=end_date)

    if search:
        messages = messages.filter(
            Q(contact_name__icontains=search) |
            Q(phone_number__icontains=search) |
            Q(content__icontains=search) |
            Q(group_name__icontains=search)
        )

    # Estatísticas para os cards
    total_messages = messages.count()
    sent_count = messages.filter(direction='sent').count()
    received_count = messages.filter(direction='received').count()
    text_count = messages.filter(message_type='text').count()
    media_count = messages.exclude(message_type='text').count()
    group_count = messages.filter(is_group=True).count()

    # Paginação
    paginator = Paginator(messages, 50)
    page = request.GET.get('page')
    messages_page = paginator.get_page(page)

    # Lista de dispositivos e chats para os filtros
    devices = Device.objects.filter(user=user)
    chats = WhatsAppChat.objects.filter(device__user=user).order_by('contact_name')

    context = {
        'messages': messages_page,
        'devices': devices,
        'chats': chats,
        'total_messages': total_messages,
        'sent_count': sent_count,
        'received_count': received_count,
        'text_count': text_count,
        'media_count': media_count,
        'group_count': group_count,
        'device_filter': device_id,
        'chat_filter': chat_id,
        'direction_filter': direction,
        'type_filter': message_type,
        'start_date': start_date,
        'end_date': end_date,
        'search': search,
        'is_paginated': messages_page.has_other_pages(),
    }

    return render(request, 'whatsapp/list.html', context)


@login_required
def whatsapp_chats(request):
    """
    Lista todos os chats do WhatsApp
    """
    user = request.user

    chats = WhatsAppChat.objects.filter(
        device__user=user
    ).order_by('-last_message_date')

    # Filtros
    search = request.GET.get('search')
    is_group = request.GET.get('is_group')
    is_archived = request.GET.get('is_archived')

    if search:
        chats = chats.filter(
            Q(contact_name__icontains=search) |
            Q(phone_number__icontains=search) |
            Q(group_name__icontains=search)
        )

    if is_group:
        chats = chats.filter(is_group=(is_group.lower() == 'true'))

    if is_archived:
        chats = chats.filter(is_archived=(is_archived.lower() == 'true'))

    # Estatísticas
    total_chats = chats.count()
    group_chats = chats.filter(is_group=True).count()
    private_chats = chats.filter(is_group=False).count()
    archived_chats = chats.filter(is_archived=True).count()

    # CORREÇÃO: Usar a chave 'total_unread' em vez de 'unread_count__sum'
    from django.db.models import Sum
    total_unread_result = chats.aggregate(total_unread=Sum('unread_count'))
    total_unread = total_unread_result['total_unread'] or 0

    # Paginação
    paginator = Paginator(chats, 20)
    page = request.GET.get('page')
    chats_page = paginator.get_page(page)

    context = {
        'chats': chats_page,
        'total_chats': total_chats,
        'group_chats': group_chats,
        'private_chats': private_chats,
        'archived_chats': archived_chats,
        'total_unread': total_unread,
        'search': search,
        'is_group_filter': is_group,
        'is_archived_filter': is_archived,
        'is_paginated': chats_page.has_other_pages(),
    }

    return render(request, 'whatsapp/chats.html', context)
@login_required
def whatsapp_chat_detail(request, chat_id):
    """
    Detalhes de um chat específico com todas as mensagens
    """
    user = request.user

    chat = get_object_or_404(
        WhatsAppChat,
        chat_id=chat_id,
        device__user=user
    )

    messages = WhatsAppMessage.objects.filter(
        device__user=user,
        chat_id=chat_id,
        is_deleted=False
    ).order_by('message_date')

    # Marcar mensagens como lidas
    messages.filter(direction='received', is_read=False).update(is_read=True)

    # Atualizar contador de não lidas no chat
    if chat.unread_count > 0:
        chat.unread_count = 0
        chat.save()

    # Estatísticas do chat
    total_messages = messages.count()
    sent_count = messages.filter(direction='sent').count()
    received_count = messages.filter(direction='received').count()
    media_count = messages.exclude(message_type='text').count()

    # Paginação
    paginator = Paginator(messages, 100)
    page = request.GET.get('page')
    messages_page = paginator.get_page(page)

    context = {
        'chat': chat,
        'messages': messages_page,
        'total_messages': total_messages,
        'sent_count': sent_count,
        'received_count': received_count,
        'media_count': media_count,
        'is_paginated': messages_page.has_other_pages(),
    }

    return render(request, 'whatsapp/chat_detail.html', context)


@login_required
def whatsapp_message_detail(request, message_id):
    """
    Detalhes de uma mensagem específica
    """
    message = get_object_or_404(
        WhatsAppMessage.objects.select_related('device'),
        id=message_id,
        device__user=request.user
    )

    # Busca outras mensagens da mesma conversa
    conversation = WhatsAppMessage.objects.filter(
        device__user=request.user,
        chat_id=message.chat_id
    ).exclude(id=message.id).order_by('-message_date')[:20]

    context = {
        'message': message,
        'conversation': conversation,
    }

    return render(request, 'whatsapp/message_detail.html', context)


@login_required
def whatsapp_statistics(request):
    """
    Estatísticas detalhadas do WhatsApp
    """
    user = request.user
    messages = WhatsAppMessage.objects.filter(device__user=user)
    chats = WhatsAppChat.objects.filter(device__user=user)

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
            'text': period_messages.filter(message_type='text').count(),
            'image': period_messages.filter(message_type='image').count(),
            'audio': period_messages.filter(message_type='audio').count(),
            'video': period_messages.filter(message_type='video').count(),
            'document': period_messages.filter(message_type='document').count(),
            'deleted': period_messages.filter(is_deleted=True).count(),
        }

    # Estatísticas de chats
    chat_stats = {
        'total': chats.count(),
        'groups': chats.filter(is_group=True).count(),
        'private': chats.filter(is_group=False).count(),
        'archived': chats.filter(is_archived=True).count(),
        'muted': chats.filter(is_muted=True).count(),
    }

    # CORREÇÃO AQUI: Calcular total_unread separadamente com a chave correta
    from django.db.models import Sum

    # Usando a chave 'total_unread' em vez de 'unread_count__sum'
    total_unread_result = chats.aggregate(total_unread=Sum('unread_count'))
    chat_stats['total_unread'] = total_unread_result['total_unread'] or 0

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
        received=Count('id', filter=Q(direction='received')),
        text=Count('id', filter=Q(message_type='text')),
        media=Count('id', filter=~Q(message_type='text'))
    ).order_by('date')

    # Preparar dados para o gráfico
    chart_labels = []
    chart_sent = []
    chart_received = []
    chart_text = []
    chart_media = []

    for day in daily_stats:
        chart_labels.append(day['date'].strftime('%d/%m'))
        chart_sent.append(day['sent'])
        chart_received.append(day['received'])
        chart_text.append(day['text'])
        chart_media.append(day['media'])

    context = {
        'periods': periods,
        'chat_stats': chat_stats,
        'device_stats': device_stats,
        'top_contacts': top_contacts,
        'chart_labels': chart_labels,
        'chart_sent': chart_sent,
        'chart_received': chart_received,
        'chart_text': chart_text,
        'chart_media': chart_media,
    }

    return render(request, 'whatsapp/statistics.html', context)

@login_required
def whatsapp_export(request):
    """
    Exporta mensagens do WhatsApp em formato CSV
    """
    user = request.user
    messages = WhatsAppMessage.objects.filter(
        device__user=user
    ).select_related('device').order_by('-message_date')

    # Aplicar filtros se fornecidos
    chat_id = request.GET.get('chat')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    if chat_id:
        messages = messages.filter(chat_id=chat_id)

    if start_date:
        messages = messages.filter(message_date__date__gte=start_date)

    if end_date:
        messages = messages.filter(message_date__date__lte=end_date)

    # Criar resposta CSV
    response = HttpResponse(content_type='text/csv')
    filename = f'whatsapp_{timezone.now().strftime("%Y%m%d_%H%M%S")}.csv'
    response['Content-Disposition'] = f'attachment; filename="{filename}"'

    writer = csv.writer(response)

    # Cabeçalho
    writer.writerow([
        'Data',
        'Hora',
        'Tipo',
        'Direção',
        'Contato',
        'Número',
        'Grupo',
        'Conteúdo',
        'Tipo Mídia',
        'Dispositivo',
        'Lida',
        'Deletada'
    ])

    # Dados
    for msg in messages:
        writer.writerow([
            msg.message_date.strftime('%d/%m/%Y'),
            msg.message_date.strftime('%H:%M:%S'),
            'Grupo' if msg.is_group else 'Privado',
            'Enviada' if msg.direction == 'sent' else 'Recebida',
            msg.contact_name or '',
            msg.phone_number,
            msg.group_name or '',
            msg.content[:200] + ('...' if len(msg.content) > 200 else ''),
            msg.get_message_type_display(),
            msg.device.device_name,
            'Sim' if msg.is_read else 'Não',
            'Sim' if msg.is_deleted else 'Não'
        ])

    return response


@login_required
def whatsapp_delete_message(request, message_id):
    """
    Marca uma mensagem como deletada
    """
    message = get_object_or_404(
        WhatsAppMessage,
        id=message_id,
        device__user=request.user
    )

    if request.method == 'POST':
        message.is_deleted = True
        message.deleted_at = timezone.now()
        message.original_content = message.content
        message.content = "[Mensagem apagada]"
        message.save()

        messages.success(request, 'Mensagem removida com sucesso.')
        return redirect('whatsapp_chat_detail', chat_id=message.chat_id)

    context = {
        'message': message
    }

    return render(request, 'whatsapp/delete.html', context)


@login_required
def whatsapp_archive_chat(request, chat_id):
    """
    Arquiva um chat
    """
    chat = get_object_or_404(
        WhatsAppChat,
        chat_id=chat_id,
        device__user=request.user
    )

    chat.is_archived = True
    chat.save()

    messages.success(request, f'Chat {chat.contact_name} arquivado com sucesso.')
    return redirect('whatsapp_chats')


@login_required
def whatsapp_unarchive_chat(request, chat_id):
    """
    Desarquiva um chat
    """
    chat = get_object_or_404(
        WhatsAppChat,
        chat_id=chat_id,
        device__user=request.user
    )

    chat.is_archived = False
    chat.save()

    messages.success(request, f'Chat {chat.contact_name} desarquivado com sucesso.')
    return redirect('whatsapp_chats')


@login_required
def whatsapp_mute_chat(request, chat_id):
    """
    Muta um chat
    """
    chat = get_object_or_404(
        WhatsAppChat,
        chat_id=chat_id,
        device__user=request.user
    )

    hours = int(request.POST.get('hours', 24))
    chat.is_muted = True
    chat.mute_expiration = timezone.now() + timedelta(hours=hours)
    chat.save()

    messages.success(request, f'Chat {chat.contact_name} silenciado por {hours} horas.')
    return redirect('whatsapp_chat_detail', chat_id=chat.chat_id)


@login_required
def whatsapp_unmute_chat(request, chat_id):
    """
    Desmuta um chat
    """
    chat = get_object_or_404(
        WhatsAppChat,
        chat_id=chat_id,
        device__user=request.user
    )

    chat.is_muted = False
    chat.mute_expiration = None
    chat.save()

    messages.success(request, f'Chat {chat.contact_name} ativado.')
    return redirect('whatsapp_chat_detail', chat_id=chat.chat_id)