from django.contrib import admin
from django.contrib import admin
from .models import Screenshot


@admin.register(Screenshot)
class ScreenshotAdmin(admin.ModelAdmin):
    list_display = ['id', 'device', 'timestamp', 'file_size', 'is_viewed']
    list_filter = ['is_viewed', 'timestamp']
    search_fields = ['device__device_name', 'device__device_id']
    readonly_fields = ['id', 'timestamp', 'uploaded_at', 'file_size']
    date_hierarchy = 'timestamp'

    fieldsets = (
        ('Informações da Imagem', {
            'fields': ('device', 'image', 'timestamp')
        }),
        ('Metadados', {
            'fields': ('file_size', 'is_viewed', 'id', 'uploaded_at')
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('device')