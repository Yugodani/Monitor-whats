from django.db import models
from apps.devices.models import Device
import uuid


class WhatsAppMessage(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    device = models.ForeignKey(Device, on_delete=models.CASCADE, related_name='whatsapp_messages')

    phone_number = models.CharField(max_length=20, blank=True)
    contact_name = models.CharField(max_length=255, blank=True, null=True)
    content = models.TextField()
    message_date = models.DateTimeField()
    direction = models.CharField(max_length=10)  # 'sent' ou 'received'
    is_read = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)

    class Meta:
        ordering = ['-message_date']
        db_table = 'whatsapp_messages'

    def __str__(self):
        return f"{self.contact_name or self.phone_number} - {self.message_date}"