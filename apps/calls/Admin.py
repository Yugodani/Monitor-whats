from django.contrib import admin
from .models import Call


@admin.register(Call)
class CallAdmin(admin.ModelAdmin):
    list_display = ['id', 'phone_number', 'call_type', 'duration', 'call_date', 'device', 'is_deleted']
    list_filter = ['call_type', 'is_deleted', 'call_date']
    search_fields = ['phone_number', 'contact_name']
    readonly_fields = ['id', 'synced_at']
    date_hierarchy = 'call_date'
    ordering = ['-call_date']

    fieldsets = (
        ('Informações da Ligação', {
            'fields': ('phone_number', 'contact_name', 'call_type', 'duration', 'call_date')
        }),
        ('Dispositivo', {
            'fields': ('device', 'synced_at', 'is_deleted')
        }),
        ('Metadados', {
            'fields': ('id',),
            'classes': ('collapse',)
        })
    )