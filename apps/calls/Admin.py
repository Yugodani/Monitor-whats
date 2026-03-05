from django.contrib import admin
from .models import Call

class CallAdmin(admin.ModelAdmin):
    list_display = ['phone_number', 'call_type', 'call_date']

admin.site.register(Call, CallAdmin)  # ← Registro explícito