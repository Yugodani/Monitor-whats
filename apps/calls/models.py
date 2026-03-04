from django.db import models
from apps.devices.models import Device
import uuid


class Call(models.Model):
    CALL_TYPE_CHOICES = [
        ('incoming', 'Recebida'),
        ('outgoing', 'Realizada'),
        ('missed', 'Perdida'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    device = models.ForeignKey(Device, on_delete=models.CASCADE, related_name='calls')

    phone_number = models.CharField(max_length=20)
    contact_name = models.CharField(max_length=255, blank=True, null=True)
    call_type = models.CharField(max_length=20, choices=CALL_TYPE_CHOICES)
    duration = models.IntegerField(default=0)  # segundos
    call_date = models.DateTimeField()

    synced_at = models.DateTimeField(auto_now_add=True)
    is_deleted = models.BooleanField(default=False)

    sim_slot = models.IntegerField(null=True, blank=True)
    imei = models.CharField(max_length=50, blank=True)
    location = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ['-call_date']
        db_table = 'calls_call'

    def __str__(self):
        return f"{self.phone_number} - {self.call_date}"