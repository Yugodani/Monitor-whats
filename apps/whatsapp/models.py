from django.db import models
from django.conf import settings
import uuid


class WhatsAppMessage(models.Model):
    MESSAGE_TYPE_CHOICES = [
        ('text', 'Texto'),
        ('image', 'Imagem'),
        ('audio', 'Áudio'),
        ('video', 'Vídeo'),
        ('document', 'Documento'),
        ('location', 'Localização'),
        ('contact', 'Contato'),
    ]

    DIRECTION_CHOICES = [
        ('sent', 'Enviada'),
        ('received', 'Recebida'),
    ]

    STATUS_CHOICES = [
        ('sent', 'Enviada'),
        ('delivered', 'Entregue'),
        ('read', 'Lida'),
        ('failed', 'Falhou'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    device = models.ForeignKey('devices.Device', on_delete=models.CASCADE, related_name='whatsapp_messages')

    # Message identifiers
    whatsapp_message_id = models.CharField(max_length=255, unique=True)
    chat_id = models.CharField(max_length=255, db_index=True)

    # Contact info
    contact_name = models.CharField(max_length=255, blank=True, null=True)
    phone_number = models.CharField(max_length=20, db_index=True)
    is_group = models.BooleanField(default=False)
    group_name = models.CharField(max_length=255, blank=True)

    # Message details
    direction = models.CharField(max_length=20, choices=DIRECTION_CHOICES)
    message_type = models.CharField(max_length=20, choices=MESSAGE_TYPE_CHOICES, default='text')
    content = models.TextField()

    # Media
    media_url = models.URLField(blank=True, null=True)
    media_path = models.CharField(max_length=500, blank=True)
    media_size = models.IntegerField(null=True, blank=True)
    media_duration = models.IntegerField(null=True, blank=True)  # For audio/video

    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='sent')
    is_read = models.BooleanField(default=False)

    # Timestamps
    message_date = models.DateTimeField(db_index=True)
    synced_at = models.DateTimeField(auto_now_add=True)

    # Deleted messages
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)
    original_content = models.TextField(blank=True)

    # Quotes/Replies
    quoted_message_id = models.CharField(max_length=255, blank=True)
    quoted_content = models.TextField(blank=True)

    def __str__(self):
        return f"WhatsApp {self.direction} - {self.phone_number} - {self.message_date}"

    class Meta:
        db_table = 'whatsapp_messages'
        ordering = ['-message_date']
        indexes = [
            models.Index(fields=['device', 'message_date']),
            models.Index(fields=['chat_id', 'message_date']),
            models.Index(fields=['whatsapp_message_id']),
            models.Index(fields=['is_deleted']),
        ]


class WhatsAppChat(models.Model):
    """Represents a WhatsApp chat/conversation"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    device = models.ForeignKey('devices.Device', on_delete=models.CASCADE, related_name='whatsapp_chats')

    chat_id = models.CharField(max_length=255, unique=True)
    contact_name = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=20)
    is_group = models.BooleanField(default=False)

    # Last message info
    last_message = models.TextField(blank=True)
    last_message_date = models.DateTimeField()
    last_message_type = models.CharField(max_length=20, blank=True)

    # Statistics
    total_messages = models.IntegerField(default=0)
    unread_count = models.IntegerField(default=0)

    # Settings
    is_archived = models.BooleanField(default=False)
    is_muted = models.BooleanField(default=False)
    mute_expiration = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'whatsapp_chats'
        ordering = ['-last_message_date']