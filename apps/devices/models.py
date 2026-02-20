from django.db import models
from django.conf import settings
import uuid


class Device(models.Model):
    STATUS_CHOICES = [
        ('active', 'Ativo'),
        ('inactive', 'Inativo'),
        ('blocked', 'Bloqueado'),
        ('maintenance', 'Em Manutenção'),
    ]

    OS_CHOICES = [
        ('android', 'Android'),
        ('ios', 'iOS'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    device_id = models.CharField(max_length=255, unique=True)
    device_name = models.CharField(max_length=255)
    device_model = models.CharField(max_length=255, blank=True)
    manufacturer = models.CharField(max_length=255, blank=True)
    os_type = models.CharField(max_length=50, choices=OS_CHOICES)
    os_version = models.CharField(max_length=50, blank=True)
    app_version = models.CharField(max_length=50, blank=True)
    phone_number = models.CharField(max_length=20, blank=True)
    imei = models.CharField(max_length=50, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')

    # Owner
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='devices')
    assigned_to = models.CharField(max_length=255, blank=True, help_text='Nome do colaborador')

    # Timestamps
    last_sync = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Metadata
    battery_level = models.IntegerField(null=True, blank=True)
    storage_used = models.BigIntegerField(null=True, blank=True)
    is_rooted = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.device_name} - {self.device_id}"

    class Meta:
        db_table = 'devices_device'
        verbose_name = 'Dispositivo'
        verbose_name_plural = 'Dispositivos'
        indexes = [
            models.Index(fields=['device_id']),
            models.Index(fields=['user', 'status']),
            models.Index(fields=['last_sync']),
        ]


class DeviceLog(models.Model):
    LOG_TYPES = [
        ('info', 'Informação'),
        ('warning', 'Aviso'),
        ('error', 'Erro'),
        ('sync', 'Sincronização'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    device = models.ForeignKey(Device, on_delete=models.CASCADE, related_name='logs')
    log_type = models.CharField(max_length=20, choices=LOG_TYPES)
    message = models.TextField()
    details = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.device.device_name} - {self.log_type} - {self.created_at}"

    class Meta:
        db_table = 'devices_log'
        verbose_name = 'Log do Dispositivo'
        verbose_name_plural = 'Logs dos Dispositivos'
        ordering = ['-created_at']