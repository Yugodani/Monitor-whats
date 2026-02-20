"""
Modelos para o app sms_messages
"""
from django.db import models
import uuid

class SMSMessage(models.Model):
    MESSAGE_TYPE_CHOICES = [
        ('sms', 'SMS'),
        ('mms', 'MMS'),
    ]

    DIRECTION_CHOICES = [
        ('sent', 'Enviada'),
        ('received', 'Recebida'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    device = models.ForeignKey('devices.Device', on_delete=models.CASCADE, related_name='messages')

    phone_number = models.CharField(max_length=20, db_index=True)
    contact_name = models.CharField(max_length=255, blank=True, null=True)
    message_type = models.CharField(max_length=20, choices=MESSAGE_TYPE_CHOICES, default='sms')
    direction = models.CharField(max_length=20, choices=DIRECTION_CHOICES)
    content = models.TextField()
    message_date = models.DateTimeField(db_index=True)
    is_read = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)

    class Meta:
        db_table = 'sms_messages'
        ordering = ['-message_date']
