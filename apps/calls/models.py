from django.db import models
from django.conf import settings
import uuid


class Call(models.Model):
    CALL_TYPE_CHOICES = [
        ('incoming', 'Recebida'),
        ('outgoing', 'Realizada'),
        ('missed', 'Perdida'),
        ('rejected', 'Rejeitada'),
        ('blocked', 'Bloqueada'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    device = models.ForeignKey('devices.Device', on_delete=models.CASCADE, related_name='calls')

    # Call details
    phone_number = models.CharField(max_length=20)
    contact_name = models.CharField(max_length=255, blank=True, null=True)
    call_type = models.CharField(max_length=20, choices=CALL_TYPE_CHOICES)
    duration = models.IntegerField(default=0, help_text='Duração em segundos')

    # Timestamps
    call_date = models.DateTimeField(db_index=True)
    synced_at = models.DateTimeField(auto_now_add=True)

    # Additional info
    sim_slot = models.IntegerField(null=True, blank=True)
    imei = models.CharField(max_length=50, blank=True)
    location = models.CharField(max_length=255, blank=True)

    # Metadata
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.call_type} - {self.phone_number} - {self.duration}s"

    class Meta:
        db_table = 'calls_call'
        ordering = ['-call_date']
        indexes = [
            models.Index(fields=['device', 'call_date']),
            models.Index(fields=['phone_number']),
            models.Index(fields=['call_type']),
        ]