from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView
from django.http import JsonResponse
from django.db import connection
from django.core.management import call_command
from django.views.decorators.csrf import csrf_exempt
import io
import sys
import os

@csrf_exempt
def reset_and_migrate(request):
    """
    ENDPOINT PERIGOSO - APAGA TODOS OS DADOS!
    Use apenas se o migrate normal falhar
    """
    SECRET_KEY = 'Nota102030@'

    key = request.GET.get('key', '')
    if key != SECRET_KEY:
        return JsonResponse({'error': 'Não autorizado'}, status=403)

    try:
        from django.db import connection

        # RESET COMPLETO - APAGA TUDO!
        with connection.cursor() as cursor:
            cursor.execute('DROP SCHEMA public CASCADE;')
            cursor.execute('CREATE SCHEMA public;')
            cursor.execute('GRANT ALL ON SCHEMA public TO public;')

        # Executar migrações
        output = io.StringIO()
        sys.stdout = output
        call_command('migrate', verbosity=2, interactive=False)
        sys.stdout = sys.__stdout__

        return JsonResponse({
            'status': 'success',
            'message': 'Banco resetado e migrações aplicadas!',
            'output': output.getvalue()
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

def run_migrations_now(request):
    """
    ENDPOINT TEMPORÁRIO - Execute UMA ÚNICA VEZ e depois REMOVA!
    Acesse: /debug/force-migrate/?key=sua-chave-secreta
    """
    # Chave de segurança - mude para algo seguro
    SECRET_KEY = 'Nota102030@'

    # Verificar autorização
    key = request.GET.get('key', '')
    if key != SECRET_KEY:
        return JsonResponse({'error': 'Não autorizado'}, status=403)

    # Executar migrações
    try:
        output = io.StringIO()
        sys.stdout = output

        # Ordem correta das migrações
        call_command('migrate', 'accounts', verbosity=2, interactive=False)
        call_command('migrate', 'devices', verbosity=2, interactive=False)
        call_command('migrate', 'calls', verbosity=2, interactive=False)
        call_command('migrate', 'sms_messages', verbosity=2, interactive=False)
        call_command('migrate', 'whatsapp', verbosity=2, interactive=False)
        call_command('migrate', 'mobile_api', verbosity=2, interactive=False)
        call_command('migrate', verbosity=2, interactive=False)

        sys.stdout = sys.__stdout__

        return JsonResponse({
            'status': 'success',
            'message': 'Migrações executadas com sucesso!',
            'output': output.getvalue()
        })
    except Exception as e:
        sys.stdout = sys.__stdout__
        return JsonResponse({
            'status': 'error',
            'error': str(e)
        }, status=500)


def run_migrations(request):
    """
    Endpoint para executar migrações via HTTP (use com MUITO cuidado!)
    """
    # Proteger com uma chave secreta para não expor
    secret_key = request.GET.get('secret', '')
    if secret_key != 'sua-chave-secreta-temporaria':
        return JsonResponse({'error': 'Não autorizado'}, status=403)

    try:
        # Capturar output das migrações
        output = io.StringIO()
        sys.stdout = output

        # Executar migrações
        call_command('migrate', verbosity=2, interactive=False)

        # Restaurar stdout
        sys.stdout = sys.__stdout__

        return JsonResponse({
            'status': 'success',
            'output': output.getvalue()
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'error': str(e)
        }, status=500)


def check_db(request):
    """Endpoint para verificar status do banco"""
    from django.db import connections
    from django.db.utils import OperationalError

    info = {
        'status': 'unknown',
        'database_url': 'definida' if os.environ.get('DATABASE_URL') else 'NÃO DEFINIDA',
        'debug': settings.DEBUG,
    }

    # Testar conexão
    try:
        connections['default'].cursor()
        info['connection'] = 'OK'
    except OperationalError as e:
        info['connection'] = f'ERRO: {str(e)}'
        info['status'] = 'error'
        return JsonResponse(info)

    # Listar tabelas
    from django.db import connection
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name;
        """)
        tables = [row[0] for row in cursor.fetchall()]

        info['status'] = 'connected'
        info['tables'] = tables
        info['tables_count'] = len(tables)
        info['has_user_table'] = 'accounts_user' in tables

        # Contar usuários se a tabela existir
        if 'accounts_user' in tables:
            cursor.execute("SELECT COUNT(*) FROM accounts_user;")
            info['user_count'] = cursor.fetchone()[0]
        else:
            info['user_count'] = 0

    return JsonResponse(info)

urlpatterns = [
    path('debug/force-migrate/', run_migrations_now),
    path('debug/check-db/', check_db),  # que você já tem
    path('admin/', admin.site.urls),
    path('debug/run-migrations/', run_migrations),
    path('admin/', admin.site.urls),

    # API URLs
    path('api/auth/', include('apps.accounts.urls')),
    path('api/devices/', include('apps.devices.urls')),
    path('api/calls/', include('apps.calls.urls')),
    path('api/messages/', include('apps.sms_messages.urls')),
    path('api/whatsapp/', include('apps.whatsapp.urls')),
    path('api/mobile/', include('mobile_api.urls')),

    # Web URLs
    path('', RedirectView.as_view(url='/dashboard/')),
    path('', include('apps.accounts.urls_web')),
    path('', include('apps.devices.urls_web')),
    path('', include('apps.calls.urls_web')),
    path('', include('apps.sms_messages.urls_web')),
    path('', include('apps.whatsapp.urls_web')),  # ADICIONAR ESTA LINHA
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)