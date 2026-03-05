from django.contrib import admin
from .models import Device, DeviceLog

@admin.register(Device)
class DeviceAdmin(admin.ModelAdmin):
    list_display = ['device_name', 'device_model', 'user', 'status', 'last_sync']
    list_filter = ['status', 'os_type']
    search_fields = ['device_name', 'device_model', 'phone_number']

@admin.register(DeviceLog)
class DeviceLogAdmin(admin.ModelAdmin):
    list_display = ['device', 'log_type', 'created_at']
    list_filter = ['log_type']
    date_hierarchy = 'created_at'