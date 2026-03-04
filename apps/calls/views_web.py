from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q, Count, Sum
from .models import Call
from apps.devices.models import Device


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
    """Estatísticas de ligações"""
    user = request.user
    calls = Call.objects.filter(device__user=user)

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
        },
        'week': {
            'total': calls.filter(call_date__date__gte=week_ago).count(),
            'incoming': calls.filter(call_date__date__gte=week_ago, call_type='incoming').count(),
            'outgoing': calls.filter(call_date__date__gte=week_ago, call_type='outgoing').count(),
            'missed': calls.filter(call_date__date__gte=week_ago, call_type='missed').count(),
        },
        'month': {
            'total': calls.filter(call_date__date__gte=month_ago).count(),
            'incoming': calls.filter(call_date__date__gte=month_ago, call_type='incoming').count(),
            'outgoing': calls.filter(call_date__date__gte=month_ago, call_type='outgoing').count(),
            'missed': calls.filter(call_date__date__gte=month_ago, call_type='missed').count(),
        },
        'all': {
            'total': calls.count(),
            'incoming': calls.filter(call_type='incoming').count(),
            'outgoing': calls.filter(call_type='outgoing').count(),
            'missed': calls.filter(call_type='missed').count(),
        }
    }

    context = {
        'periods': periods,
    }

    return render(request, 'calls/statistics.html', context)