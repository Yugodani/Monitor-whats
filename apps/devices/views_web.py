"""
Views web para o app devices
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.utils import timezone
from datetime import timedelta

from .models import Device, DeviceLog
from apps.calls.models import Call
from apps.sms_messages.models import SMSMessage
from apps.whatsapp.models import WhatsAppMessage


@login_required
def device_list(request):
    """
    Lista todos os dispositivos do usuário
    """
    user = request.user
    devices = Device.objects.filter(user=user)

    # Filtros
    status_filter = request.GET.get('status')
    search_query = request.GET.get('search')

    if status_filter:
        devices = devices.filter(status=status_filter)

    if search_query:
        devices = devices.filter(
            Q(device_name__icontains=search_query) |
            Q(device_model__icontains=search_query) |
            Q(phone_number__icontains=search_query) |
            Q(assigned_to__icontains=search_query)
        )

    # Ordenação
    order_by = request.GET.get('order_by', '-last_sync')
    devices = devices.order_by(order_by)

    # Paginação
    paginator = Paginator(devices, 10)
    page = request.GET.get('page')
    devices_page = paginator.get_page(page)

    # Estatísticas
    total_devices = devices.count()
    active_devices = devices.filter(status='active').count()
    inactive_devices = devices.filter(status='inactive').count()
    blocked_devices = devices.filter(status='blocked').count()

    context = {
        'devices': devices_page,
        'total_devices': total_devices,
        'active_devices': active_devices,
        'inactive_devices': inactive_devices,
        'blocked_devices': blocked_devices,
        'status_filter': status_filter,
        'search_query': search_query,
    }

    return render(request, 'devices/list.html', context)


@login_required
def device_detail(request, device_id):
    """
    Detalhes de um dispositivo específico
    """
    device = get_object_or_404(Device, id=device_id, user=request.user)

    # Últimas atividades
    recent_calls = Call.objects.filter(device=device).order_by('-call_date')[:10]
    recent_messages = SMSMessage.objects.filter(device=device).order_by('-message_date')[:10]
    recent_whatsapp = WhatsAppMessage.objects.filter(device=device).order_by('-message_date')[:10]
    recent_logs = DeviceLog.objects.filter(device=device).order_by('-created_at')[:20]

    # Estatísticas do dispositivo
    total_calls = Call.objects.filter(device=device).count()
    total_messages = SMSMessage.objects.filter(device=device).count()
    total_whatsapp = WhatsAppMessage.objects.filter(device=device).count()

    # Atividade nos últimos 7 dias
    last_7_days = timezone.now() - timedelta(days=7)
    calls_7d = Call.objects.filter(device=device, call_date__gte=last_7_days).count()
    messages_7d = SMSMessage.objects.filter(device=device, message_date__gte=last_7_days).count()
    whatsapp_7d = WhatsAppMessage.objects.filter(device=device, message_date__gte=last_7_days).count()

    context = {
        'device': device,
        'recent_calls': recent_calls,
        'recent_messages': recent_messages,
        'recent_whatsapp': recent_whatsapp,
        'recent_logs': recent_logs,
        'total_calls': total_calls,
        'total_messages': total_messages,
        'total_whatsapp': total_whatsapp,
        'calls_7d': calls_7d,
        'messages_7d': messages_7d,
        'whatsapp_7d': whatsapp_7d,
    }

    return render(request, 'devices/detail.html', context)


@login_required
def device_logs(request, device_id):
    """
    Logs de um dispositivo específico
    """
    device = get_object_or_404(Device, id=device_id, user=request.user)
    logs = DeviceLog.objects.filter(device=device).order_by('-created_at')

    # Filtros
    log_type = request.GET.get('type')
    if log_type:
        logs = logs.filter(log_type=log_type)

    # Paginação
    paginator = Paginator(logs, 50)
    page = request.GET.get('page')
    logs_page = paginator.get_page(page)

    context = {
        'device': device,
        'logs': logs_page,
        'log_type': log_type,
    }

    return render(request, 'devices/logs.html', context)


@login_required
def device_add(request):
    """
    Adiciona um novo dispositivo manualmente
    """
    if request.method == 'POST':
        device_id = request.POST.get('device_id')
        device_name = request.POST.get('device_name')
        device_model = request.POST.get('device_model')
        manufacturer = request.POST.get('manufacturer')
        os_type = request.POST.get('os_type')
        phone_number = request.POST.get('phone_number')
        assigned_to = request.POST.get('assigned_to')

        # Validação básica
        if not device_id or not device_name:
            messages.error(request, 'ID do dispositivo e nome são obrigatórios')
            return redirect('device_add')

        # Verifica se já existe
        if Device.objects.filter(device_id=device_id, user=request.user).exists():
            messages.error(request, 'Este dispositivo já está cadastrado')
            return redirect('device_add')

        # Cria o dispositivo
        Device.objects.create(
            device_id=device_id,
            device_name=device_name,
            device_model=device_model,
            manufacturer=manufacturer,
            os_type=os_type,
            phone_number=phone_number,
            assigned_to=assigned_to,
            user=request.user,
            status='inactive'  # Começa como inativo até o primeiro sync
        )

        messages.success(request, 'Dispositivo adicionado com sucesso!')
        return redirect('device_list')

    return render(request, 'devices/add.html')


@login_required
def device_edit(request, device_id):
    """
    Edita um dispositivo existente
    """
    device = get_object_or_404(Device, id=device_id, user=request.user)

    if request.method == 'POST':
        device.device_name = request.POST.get('device_name', device.device_name)
        device.device_model = request.POST.get('device_model', device.device_model)
        device.manufacturer = request.POST.get('manufacturer', device.manufacturer)
        device.phone_number = request.POST.get('phone_number', device.phone_number)
        device.assigned_to = request.POST.get('assigned_to', device.assigned_to)
        device.status = request.POST.get('status', device.status)
        device.save()

        messages.success(request, 'Dispositivo atualizado com sucesso!')
        return redirect('device_detail', device_id=device.id)

    context = {
        'device': device
    }

    return render(request, 'devices/edit.html', context)


@login_required
def device_delete(request, device_id):
    """
    Remove um dispositivo
    """
    device = get_object_or_404(Device, id=device_id, user=request.user)

    if request.method == 'POST':
        device.delete()
        messages.success(request, 'Dispositivo removido com sucesso!')
        return redirect('device_list')

    context = {
        'device': device
    }

    return render(request, 'devices/delete.html', context)


@login_required
def device_sync(request, device_id):
    """
    Força sincronização de um dispositivo
    """
    device = get_object_or_404(Device, id=device_id, user=request.user)

    device.last_sync = timezone.now()
    device.save()

    # Cria log
    DeviceLog.objects.create(
        device=device,
        log_type='sync',
        message='Sincronização forçada via web',
        details={'user': request.user.email}
    )

    messages.success(request, f'Sincronização solicitada para {device.device_name}')
    return redirect('device_detail', device_id=device.id)


@login_required
def device_block(request, device_id):
    """
    Bloqueia um dispositivo
    """
    device = get_object_or_404(Device, id=device_id, user=request.user)

    device.status = 'blocked'
    device.save()

    DeviceLog.objects.create(
        device=device,
        log_type='warning',
        message='Dispositivo bloqueado via web',
        details={'user': request.user.email}
    )

    messages.warning(request, f'Dispositivo {device.device_name} bloqueado')
    return redirect('device_detail', device_id=device.id)


@login_required
def device_unblock(request, device_id):
    """
    Desbloqueia um dispositivo
    """
    device = get_object_or_404(Device, id=device_id, user=request.user)

    device.status = 'active'
    device.save()

    DeviceLog.objects.create(
        device=device,
        log_type='info',
        message='Dispositivo desbloqueado via web',
        details={'user': request.user.email}
    )

    messages.success(request, f'Dispositivo {device.device_name} desbloqueado')
    return redirect('device_detail', device_id=device.id)