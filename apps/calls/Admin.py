from django.contrib import admin
from .models import Call

@admin.register(Call)
class CallAdmin(admin.ModelAdmin):
    list_display = ['phone_number', 'call_type', 'duration', 'call_date', 'device']
    list_filter = ['call_type', 'call_date']
    search_fields = ['phone_number', 'contact_name']
    date_hierarchy = 'call_date'