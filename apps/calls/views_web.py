"""
Views web para o app calls
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Count, Sum, Avg, Max  # Avg incluído aqui
from django.utils import timezone
from django.http import HttpResponse
from datetime import datetime, timedelta
import csv

from .models import Call
from apps.devices.models import Device


@login_required
def call_list(request):
    """
    Lista todas as ligações do usuário com filtros e paginação
    """
    user = request.user

    # Busca todas as ligações dos dispositivos do usuário
    calls = Call.objects.filter(
        device__user=user
    ).select_related('device').order_by('-call_date')

    # Filtros
    device_id = request.GET.get('device')
    call_type = request.GET.get('type')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    search = request.GET.get('search')

    if device_id:
        calls = calls.filter(device_id=device_id)

    if call_type:
        calls = calls.filter(call_type=call_type)

    if start_date:
        calls = calls.filter(call_date__date__gte=start_date)

    if end_date:
        calls = calls.filter(call_date__date__lte=end_date)

    if search:
        calls = calls.filter(
            Q(phone_number__icontains=search) |
            Q(contact_name__icontains=search)
        )

    # Estatísticas para os cards
    total_calls = calls.count()
    total_duration = calls.aggregate(Sum('duration'))['duration__sum'] or 0
    avg_duration = total_duration / total_calls if total_calls > 0 else 0

    # Estatísticas por tipo
    incoming_count = calls.filter(call_type='incoming').count()
    outgoing_count = calls.filter(call_type='outgoing').count()
    missed_count = calls.filter(call_type='missed').count()

    # Paginação
    paginator = Paginator(calls, 50)
    page = request.GET.get('page')
    calls_page = paginator.get_page(page)

    # Lista de dispositivos para o filtro
    devices = Device.objects.filter(user=user)

    context = {
        'calls': calls_page,
        'devices': devices,
        'total_calls': total_calls,
        'total_duration': total_duration,
        'avg_duration': round(avg_duration, 1),
        'incoming_count': incoming_count,
        'outgoing_count': outgoing_count,
        'missed_count': missed_count,
        'device_filter': device_id,
        'type_filter': call_type,
        'start_date': start_date,
        'end_date': end_date,
        'search': search,
        'is_paginated': calls_page.has_other_pages(),
    }

    return render(request, 'calls/list.html', context)


@login_required
def call_detail(request, call_id):
    """
    Detalhes de uma ligação específica
    """
    call = get_object_or_404(
        Call.objects.select_related('device'),
        id=call_id,
        device__user=request.user
    )

    # Busca outras ligações do mesmo número
    same_number_calls = Call.objects.filter(
        device__user=request.user,
        phone_number=call.phone_number
    ).exclude(id=call.id).order_by('-call_date')[:10]

    context = {
        'call': call,
        'same_number_calls': same_number_calls,
        'duration_minutes': call.duration // 60,
        'duration_seconds': call.duration % 60,
    }

    return render(request, 'calls/detail.html', context)


@login_required
def call_statistics(request):
    """
    Estatísticas detalhadas de ligações com gráficos
    """
    user = request.user
    calls = Call.objects.filter(device__user=user)

    # Períodos para análise
    today = timezone.now().date()
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)

    # Estatísticas por período
    periods = {}

    # Hoje
    today_calls = calls.filter(call_date__date=today)
    periods['today'] = {
        'total': today_calls.count(),
        'duration': today_calls.aggregate(Sum('duration'))['duration__sum'] or 0,
        'incoming': today_calls.filter(call_type='incoming').count(),
        'outgoing': today_calls.filter(call_type='outgoing').count(),
        'missed': today_calls.filter(call_type='missed').count(),
        'avg_duration': today_calls.aggregate(Avg('duration'))['duration__avg'] or 0,
    }

    # Últimos 7 dias
    week_calls = calls.filter(call_date__date__gte=week_ago)
    periods['week'] = {
        'total': week_calls.count(),
        'duration': week_calls.aggregate(Sum('duration'))['duration__sum'] or 0,
        'incoming': week_calls.filter(call_type='incoming').count(),
        'outgoing': week_calls.filter(call_type='outgoing').count(),
        'missed': week_calls.filter(call_type='missed').count(),
        'avg_duration': week_calls.aggregate(Avg('duration'))['duration__avg'] or 0,
    }

    # Últimos 30 dias
    month_calls = calls.filter(call_date__date__gte=month_ago)
    periods['month'] = {
        'total': month_calls.count(),
        'duration': month_calls.aggregate(Sum('duration'))['duration__sum'] or 0,
        'incoming': month_calls.filter(call_type='incoming').count(),
        'outgoing': month_calls.filter(call_type='outgoing').count(),
        'missed': month_calls.filter(call_type='missed').count(),
        'avg_duration': month_calls.aggregate(Avg('duration'))['duration__avg'] or 0,
    }

    # Total geral
    periods['all'] = {
        'total': calls.count(),
        'duration': calls.aggregate(Sum('duration'))['duration__sum'] or 0,
        'incoming': calls.filter(call_type='incoming').count(),
        'outgoing': calls.filter(call_type='outgoing').count(),
        'missed': calls.filter(call_type='missed').count(),
        'avg_duration': calls.aggregate(Avg('duration'))['duration__avg'] or 0,
        'avg_duration_incoming': calls.filter(call_type='incoming').aggregate(Avg('duration'))['duration__avg'] or 0,
        'avg_duration_outgoing': calls.filter(call_type='outgoing').aggregate(Avg('duration'))['duration__avg'] or 0,
        'avg_duration_missed': calls.filter(call_type='missed').aggregate(Avg('duration'))['duration__avg'] or 0,
    }

    # Estatísticas por dispositivo
    devices = Device.objects.filter(user=user)
    device_stats = []

    for device in devices:
        device_calls = calls.filter(device=device)
        device_stats.append({
            'device': device,
            'total': device_calls.count(),
            'duration': device_calls.aggregate(Sum('duration'))['duration__sum'] or 0,
            'incoming': device_calls.filter(call_type='incoming').count(),
            'outgoing': device_calls.filter(call_type='outgoing').count(),
            'missed': device_calls.filter(call_type='missed').count(),
            'last_call': device_calls.order_by('-call_date').first().call_date if device_calls.exists() else None,
        })

    # Top 10 contatos mais chamados
    top_contacts = calls.values(
        'phone_number', 'contact_name'
    ).annotate(
        total=Count('id'),
        total_duration=Sum('duration')
    ).order_by('-total')[:10]

    # Dados para gráfico dos últimos 30 dias
    from django.db.models.functions import TruncDate

    last_30_days = timezone.now() - timedelta(days=30)
    daily_stats = calls.filter(
        call_date__gte=last_30_days
    ).annotate(
        date=TruncDate('call_date')
    ).values('date').annotate(
        total=Count('id'),
        incoming=Count('id', filter=Q(call_type='incoming')),
        outgoing=Count('id', filter=Q(call_type='outgoing')),
        missed=Count('id', filter=Q(call_type='missed'))
    ).order_by('date')

    # Preparar dados para o gráfico
    chart_labels = []
    chart_incoming = []
    chart_outgoing = []
    chart_missed = []

    for day in daily_stats:
        chart_labels.append(day['date'].strftime('%d/%m'))
        chart_incoming.append(day['incoming'])
        chart_outgoing.append(day['outgoing'])
        chart_missed.append(day['missed'])

    context = {
        'periods': periods,
        'device_stats': device_stats,
        'top_contacts': top_contacts,
        'chart_labels': chart_labels,
        'chart_incoming': chart_incoming,
        'chart_outgoing': chart_outgoing,
        'chart_missed': chart_missed,
    }

    return render(request, 'calls/statistics.html', context)


@login_required
def call_export(request):
    """
    Exporta ligações em formato CSV
    """
    user = request.user
    calls = Call.objects.filter(
        device__user=user
    ).select_related('device').order_by('-call_date')

    # Aplicar filtros se fornecidos
    device_id = request.GET.get('device')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    call_type = request.GET.get('type')

    if device_id:
        calls = calls.filter(device_id=device_id)

    if start_date:
        calls = calls.filter(call_date__date__gte=start_date)

    if end_date:
        calls = calls.filter(call_date__date__lte=end_date)

    if call_type:
        calls = calls.filter(call_type=call_type)

    # Criar resposta CSV
    response = HttpResponse(content_type='text/csv')
    filename = f'ligacoes_{timezone.now().strftime("%Y%m%d_%H%M%S")}.csv'
    response['Content-Disposition'] = f'attachment; filename="{filename}"'

    writer = csv.writer(response)

    # Cabeçalho
    writer.writerow([
        'Data',
        'Hora',
        'Tipo',
        'Número',
        'Contato',
        'Duração (s)',
        'Dispositivo',
        'IMEI',
        'Localização',
        'Status'
    ])

    # Dados
    for call in calls:
        writer.writerow([
            call.call_date.strftime('%d/%m/%Y'),
            call.call_date.strftime('%H:%M:%S'),
            call.get_call_type_display(),
            call.phone_number,
            call.contact_name or '',
            call.duration,
            call.device.device_name,
            call.imei or '',
            call.location or '',
            'Deletada' if call.is_deleted else 'Ativa'
        ])

    return response


@login_required
def call_delete(request, call_id):
    """
    Marca uma ligação como deletada (soft delete)
    """
    call = get_object_or_404(Call, id=call_id, device__user=request.user)

    if request.method == 'POST':
        call.is_deleted = True
        call.deleted_at = timezone.now()
        call.save()

        messages.success(request, 'Ligação removida com sucesso.')
        return redirect('calls')

    context = {
        'call': call
    }

    return render(request, 'calls/delete.html', context)


@login_required
def call_delete_bulk(request):
    """
    Deleta múltiplas ligações
    """
    if request.method == 'POST':
        call_ids = request.POST.getlist('call_ids')

        if call_ids:
            calls = Call.objects.filter(
                id__in=call_ids,
                device__user=request.user
            )

            count = calls.count()
            calls.update(
                is_deleted=True,
                deleted_at=timezone.now()
            )

            messages.success(request, f'{count} ligação(ns) removida(s) com sucesso.')
        else:
            messages.warning(request, 'Nenhuma ligação selecionada.')

        return redirect('calls')

    return redirect('calls')


@login_required
def call_by_number(request, phone_number):
    """
    Lista todas as ligações de um número específico
    """
    calls = Call.objects.filter(
        device__user=request.user,
        phone_number=phone_number
    ).select_related('device').order_by('-call_date')

    # Informações do contato
    first_call = calls.first()
    contact_name = first_call.contact_name if first_call else phone_number

    # Estatísticas
    total_calls = calls.count()
    total_duration = calls.aggregate(Sum('duration'))['duration__sum'] or 0
    incoming = calls.filter(call_type='incoming').count()
    outgoing = calls.filter(call_type='outgoing').count()
    missed = calls.filter(call_type='missed').count()

    # Paginação
    paginator = Paginator(calls, 50)
    page = request.GET.get('page')
    calls_page = paginator.get_page(page)

    context = {
        'calls': calls_page,
        'phone_number': phone_number,
        'contact_name': contact_name,
        'total_calls': total_calls,
        'total_duration': total_duration,
        'incoming': incoming,
        'outgoing': outgoing,
        'missed': missed,
        'is_paginated': calls_page.has_other_pages(),
    }

    return render(request, 'calls/by_number.html', context)


@login_required
def call_timeline(request):
    """
    View para timeline de ligações (para gráficos)
    """
    user = request.user
    days = int(request.GET.get('days', 30))

    start_date = timezone.now() - timedelta(days=days)
    calls = Call.objects.filter(
        device__user=user,
        call_date__gte=start_date
    )

    from django.db.models.functions import TruncDate

    daily_data = calls.annotate(
        date=TruncDate('call_date')
    ).values('date').annotate(
        total=Count('id'),
        incoming=Count('id', filter=Q(call_type='incoming')),
        outgoing=Count('id', filter=Q(call_type='outgoing')),
        missed=Count('id', filter=Q(call_type='missed'))
    ).order_by('date')

    return render(request, 'calls/timeline.html', {
        'daily_data': daily_data,
        'days': days
    })