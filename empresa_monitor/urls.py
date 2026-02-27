from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView
from django.http import JsonResponse
from django.db import connection
from django.core.management import call_command
import io
import sys


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
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name;
            """)
            tables = [row[0] for row in cursor.fetchall()]

            return JsonResponse({
                'status': 'connected',
                'tables': tables,
                'has_user_table': 'accounts_user' in tables
            })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'error': str(e)
        })


urlpatterns = [
    path('admin/', admin.site.urls),
    path('debug/run-migrations/', run_migrations),
    path('debug/check-db/', check_db),
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