from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView
from django.http import JsonResponse

def health_check(request):
    """Endpoint para verificar a saúde da aplicação"""
    import sys
    import django
    from django.db import connections
    from django.db.utils import OperationalError

    status = {
        'status': 'ok',
        'django_version': django.get_version(),
        'python_version': sys.version,
        'debug': settings.DEBUG,
        'database': 'unknown',
        'allowed_hosts': settings.ALLOWED_HOSTS,
    }

    # Test database connection
    db_conn = connections['default']
    try:
        db_conn.cursor()
        status['database'] = 'connected'
    except OperationalError:
        status['database'] = 'error'
        status['status'] = 'error'

    return JsonResponse(status)


urlpatterns = [
    path('health/', health_check),  # Adicione esta linha no início
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