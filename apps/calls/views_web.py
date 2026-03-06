from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q, Count, Sum
from .models import Call
from apps.devices.models import Device
from django.utils import timezone
from datetime import timedelta
from django.db.models import Count, Sum, Q


@login_required
def call_list(request):
    user = request.user
    print(f"🔍 Usuário: {user.email}")

    calls = Call.objects.filter(device__user=user).select_related('device')
    print(f"🔍 Total de ligações: {calls.count()}")

    for call in calls[:5]:  # Mostra as 5 primeiras
        print(f"  - {call.phone_number} - {call.call_date}")

    calls = calls.order_by('-call_date')
    # Filtros
    device_id = request.GET.get('device')
    call_type = request.GET.get('type')
    search = request.GET.get('search')

    if device_id:
        calls = calls.filter(device_id=device_id)

    if call_type:
        calls = calls.filter(call_type=call_type)

    if search:
        calls = calls.filter(
            Q(phone_number__icontains=search) |
            Q(contact_name__icontains=search)
        )

    # Paginação
    paginator = Paginator(calls, 50)
    page = request.GET.get('page')
    calls_page = paginator.get_page(page)

    # Estatísticas
    total_calls = calls.count()
    total_duration = calls.aggregate(Sum('duration'))['duration__sum'] or 0

    # Dispositivos para filtro
    devices = Device.objects.filter(user=user)

    context = {
        'calls': calls_page,
        'devices': devices,
        'total_calls': total_calls,
        'total_duration': total_duration,
        'device_filter': device_id,
        'type_filter': call_type,
        'search': search,
    }

    return render(request, 'calls/list.html', context)


@login_required
def call_statistics(request):
    """
    Estatísticas detalhadas de ligações
    """
    user = request.user
    calls = Call.objects.filter(device__user=user)

    # Períodos para análise
    today = timezone.now().date()
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)

    # Estatísticas por período
    periods = {
        'today': {
            'total': calls.filter(call_date__date=today).count(),
            'incoming': calls.filter(call_date__date=today, call_type='incoming').count(),
            'outgoing': calls.filter(call_date__date=today, call_type='outgoing').count(),
            'missed': calls.filter(call_date__date=today, call_type='missed').count(),
            'duration': calls.filter(call_date__date=today).aggregate(Sum('duration'))['duration__sum'] or 0,
        },
        'week': {
            'total': calls.filter(call_date__date__gte=week_ago).count(),
            'incoming': calls.filter(call_date__date__gte=week_ago, call_type='incoming').count(),
            'outgoing': calls.filter(call_date__date__gte=week_ago, call_type='outgoing').count(),
            'missed': calls.filter(call_date__date__gte=week_ago, call_type='missed').count(),
            'duration': calls.filter(call_date__date__gte=week_ago).aggregate(Sum('duration'))['duration__sum'] or 0,
        },
        'month': {
            'total': calls.filter(call_date__date__gte=month_ago).count(),
            'incoming': calls.filter(call_date__date__gte=month_ago, call_type='incoming').count(),
            'outgoing': calls.filter(call_date__date__gte=month_ago, call_type='outgoing').count(),
            'missed': calls.filter(call_date__date__gte=month_ago, call_type='missed').count(),
            'duration': calls.filter(call_date__date__gte=month_ago).aggregate(Sum('duration'))['duration__sum'] or 0,
        },
        'all': {
            'total': calls.count(),
            'incoming': calls.filter(call_type='incoming').count(),
            'outgoing': calls.filter(call_type='outgoing').count(),
            'missed': calls.filter(call_type='missed').count(),
            'duration': calls.aggregate(Sum('duration'))['duration__sum'] or 0,
        }
    }

    # Top 10 números mais chamados
    top_numbers = calls.values('phone_number', 'contact_name').annotate(
        total=Count('id'),
        total_duration=Sum('duration')
    ).order_by('-total')[:10]

    # Estatísticas por dispositivo
    devices = Device.objects.filter(user=user)
    device_stats = []
    for device in devices:
        device_calls = calls.filter(device=device)
        device_stats.append({
            'device': device,
            'total': device_calls.count(),
            'incoming': device_calls.filter(call_type='incoming').count(),
            'outgoing': device_calls.filter(call_type='outgoing').count(),
            'missed': device_calls.filter(call_type='missed').count(),
        })

    # Dados para gráfico (últimos 30 dias)
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
        'top_numbers': top_numbers,
        'device_stats': device_stats,
        'chart_labels': chart_labels,
        'chart_incoming': chart_incoming,
        'chart_outgoing': chart_outgoing,
        'chart_missed': chart_missed,
    }

    return render(request, 'calls/statistics.html', context)