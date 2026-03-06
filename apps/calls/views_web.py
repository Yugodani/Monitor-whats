from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Sum, Q
from django.utils import timezone  # ← ISSO ESTAVA FALTANDO!
from datetime import timedelta
from .models import Call
from apps.devices.models import Device


@login_required
def call_list(request):
    """Lista todas as ligações do usuário"""
    user = request.user
    calls = Call.objects.filter(device__user=user).select_related('device').order_by('-call_date')

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

    # Estatísticas
    total_calls = calls.count()
    total_duration = calls.aggregate(Sum('duration'))['duration__sum'] or 0

    # Dispositivos para filtro
    devices = Device.objects.filter(user=user)

    context = {
        'calls': calls,
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
    """Estatísticas detalhadas de ligações"""
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

    context = {
        'periods': periods,
        'top_numbers': top_numbers,
        'device_stats': device_stats,
    }

    return render(request, 'calls/statistics.html', context)


@login_required
def call_detail(request, call_id):
    """Detalhes de uma ligação específica"""
    call = get_object_or_404(Call, id=call_id, device__user=request.user)
    return render(request, 'calls/detail.html', {'call': call})