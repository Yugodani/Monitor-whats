from rest_framework import serializers
from .models import SMSMessage
from apps.devices.models import Device


class SMSMessageSerializer(serializers.ModelSerializer):
    device_name = serializers.ReadOnlyField(source='device.device_name')
    contact_display = serializers.SerializerMethodField()
    content_preview = serializers.SerializerMethodField()

    class Meta:
        model = SMSMessage
        fields = [
            'id', 'device', 'device_name', 'thread_id', 'phone_number',
            'contact_name', 'contact_display', 'message_type', 'direction',
            'content', 'content_preview', 'mms_url', 'message_date',
            'synced_at', 'is_read', 'is_delivered', 'is_deleted',
            'deleted_at', 'original_content'
        ]
        read_only_fields = ['id', 'synced_at', 'original_content']

    def get_contact_display(self, obj):
        return obj.contact_name or obj.phone_number

    def get_content_preview(self, obj):
        if obj.content:
            return obj.content[:100] + ('...' if len(obj.content) > 100 else '')
        return ''

    def validate_device(self, value):
        user = self.context['request'].user
        if value.user != user:
            raise serializers.ValidationError("Dispositivo não pertence ao usuário.")
        return value


class SMSMessageBulkSyncSerializer(serializers.Serializer):
    device_id = serializers.CharField(required=True)
    messages = serializers.ListField(child=serializers.DictField(), required=True)

    def validate_device_id(self, value):
        user = self.context['request'].user
        try:
            device = Device.objects.get(device_id=value, user=user)
        except Device.DoesNotExist:
            raise serializers.ValidationError("Dispositivo não encontrado.")
        return device