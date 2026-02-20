from rest_framework import serializers
from .models import WhatsAppMessage, WhatsAppChat
from apps.devices.models import Device


class WhatsAppMessageSerializer(serializers.ModelSerializer):
    device_name = serializers.ReadOnlyField(source='device.device_name')
    contact_display = serializers.SerializerMethodField()
    content_preview = serializers.SerializerMethodField()
    formatted_date = serializers.SerializerMethodField()

    class Meta:
        model = WhatsAppMessage
        fields = [
            'id', 'device', 'device_name', 'whatsapp_message_id', 'chat_id',
            'contact_name', 'phone_number', 'contact_display', 'is_group',
            'group_name', 'direction', 'message_type', 'content',
            'content_preview', 'media_url', 'media_path', 'media_size',
            'media_duration', 'status', 'is_read', 'message_date',
            'formatted_date', 'synced_at', 'is_deleted', 'deleted_at',
            'original_content', 'quoted_message_id', 'quoted_content'
        ]
        read_only_fields = ['id', 'synced_at', 'original_content']

    def get_contact_display(self, obj):
        if obj.is_group:
            return obj.group_name or f"Grupo: {obj.phone_number}"
        return obj.contact_name or obj.phone_number

    def get_content_preview(self, obj):
        if obj.content:
            return obj.content[:100] + ('...' if len(obj.content) > 100 else '')
        return f"[{obj.get_message_type_display()}]"

    def get_formatted_date(self, obj):
        """Return formatted date for display"""
        from django.utils import timezone
        now = timezone.now()
        diff = now - obj.message_date

        if diff.days == 0:
            if diff.seconds < 3600:
                minutes = diff.seconds // 60
                return f"{minutes} min atrás" if minutes > 0 else "Agora mesmo"
            else:
                return obj.message_date.strftime("%H:%M")
        elif diff.days == 1:
            return "Ontem"
        elif diff.days < 7:
            return obj.message_date.strftime("%A")
        else:
            return obj.message_date.strftime("%d/%m/%Y")

    def validate_device(self, value):
        user = self.context['request'].user
        if value.user != user:
            raise serializers.ValidationError("Dispositivo não pertence ao usuário.")
        return value


class WhatsAppChatSerializer(serializers.ModelSerializer):
    device_name = serializers.ReadOnlyField(source='device.device_name')
    last_message_preview = serializers.SerializerMethodField()
    unread_count = serializers.IntegerField()

    class Meta:
        model = WhatsAppChat
        fields = [
            'id', 'device', 'device_name', 'chat_id', 'contact_name',
            'phone_number', 'is_group', 'last_message', 'last_message_preview',
            'last_message_date', 'last_message_type', 'total_messages',
            'unread_count', 'is_archived', 'is_muted', 'mute_expiration',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_last_message_preview(self, obj):
        if obj.last_message:
            return obj.last_message[:50] + ('...' if len(obj.last_message) > 50 else '')
        return ''


class WhatsAppMessageBulkSyncSerializer(serializers.Serializer):
    """Serializer for bulk syncing WhatsApp messages from mobile"""
    device_id = serializers.CharField(required=True)
    messages = serializers.ListField(
        child=serializers.DictField(),
        required=True
    )
    chats = serializers.ListField(
        child=serializers.DictField(),
        required=False,
        default=[]
    )

    def validate_device_id(self, value):
        user = self.context['request'].user
        try:
            device = Device.objects.get(device_id=value, user=user)
        except Device.DoesNotExist:
            raise serializers.ValidationError("Dispositivo não encontrado.")
        return device


class WhatsAppChatDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for chat with additional info"""
    messages = serializers.SerializerMethodField()

    class Meta:
        model = WhatsAppChat
        fields = WhatsAppChatSerializer.Meta.fields + ['messages']

    def get_messages(self, obj):
        """Get recent messages for this chat"""
        messages = obj.whatsappmessage_set.all()[:50]
        return WhatsAppMessageSerializer(messages, many=True).data


class WhatsAppFilterSerializer(serializers.Serializer):
    """Serializer for WhatsApp filters"""
    device_id = serializers.UUIDField(required=False)
    chat_id = serializers.CharField(required=False, allow_blank=True)
    contact = serializers.CharField(required=False, allow_blank=True)
    message_type = serializers.ChoiceField(
        choices=['text', 'image', 'audio', 'video', 'document', 'location', 'contact', 'all'],
        default='all'
    )
    direction = serializers.ChoiceField(
        choices=['sent', 'received', 'all'],
        default='all'
    )
    start_date = serializers.DateTimeField(required=False)
    end_date = serializers.DateTimeField(required=False)
    include_deleted = serializers.BooleanField(default=False)
    is_group = serializers.BooleanField(required=False, allow_null=True)
    search = serializers.CharField(required=False, allow_blank=True)


class WhatsAppStatisticsSerializer(serializers.Serializer):
    """Serializer for WhatsApp statistics"""
    total_messages = serializers.IntegerField()
    deleted_messages = serializers.IntegerField()
    by_type = serializers.ListField(child=serializers.DictField())
    by_direction = serializers.ListField(child=serializers.DictField())
    by_day = serializers.ListField(child=serializers.DictField())
    top_contacts = serializers.ListField(child=serializers.DictField())
    active_chats = serializers.IntegerField()
    group_chats = serializers.IntegerField()
    media_stats = serializers.DictField()


class WhatsAppExportSerializer(serializers.Serializer):
    """Serializer for WhatsApp export options"""
    format = serializers.ChoiceField(choices=['csv', 'excel', 'pdf', 'json'])
    chat_id = serializers.CharField(required=False)
    start_date = serializers.DateField(required=False)
    end_date = serializers.DateField(required=False)
    include_media = serializers.BooleanField(default=False)
    include_deleted = serializers.BooleanField(default=False)