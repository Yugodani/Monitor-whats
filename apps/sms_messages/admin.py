from django.contrib import admin
from .models import SMSMessage

@admin.register(SMSMessage)
class SMSMessageAdmin(admin.ModelAdmin):
    list_display = ['phone_number', 'direction', 'message_date', 'is_read', 'is_deleted']
    list_filter = ['direction', 'message_type', 'is_read', 'is_deleted']
    search_fields = ['phone_number', 'contact_name', 'content']
    date_hierarchy = 'message_date'