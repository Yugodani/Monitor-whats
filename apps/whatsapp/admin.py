from django.contrib import admin
from .models import WhatsAppMessage, WhatsAppChat

@admin.register(WhatsAppMessage)
class WhatsAppMessageAdmin(admin.ModelAdmin):
    list_display = ['contact_name', 'phone_number', 'direction', 'message_type', 'message_date', 'is_read']
    list_filter = ['direction', 'message_type', 'is_read', 'is_deleted']
    search_fields = ['contact_name', 'phone_number', 'content']
    date_hierarchy = 'message_date'

@admin.register(WhatsAppChat)
class WhatsAppChatAdmin(admin.ModelAdmin):
    list_display = ['contact_name', 'phone_number', 'is_group', 'total_messages', 'unread_count']
    list_filter = ['is_group', 'is_archived', 'is_muted']
    search_fields = ['contact_name', 'phone_number', 'group_name']