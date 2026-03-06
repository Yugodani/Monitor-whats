from rest_framework import serializers
from .models import WhatsAppMessage, WhatsAppChat


class WhatsAppMessageSerializer(serializers.ModelSerializer):
    device_name = serializers.ReadOnlyField(source='device.device_name')

    class Meta:
        model = WhatsAppMessage
        fields = '__all__'
        read_only_fields = ['id', 'synced_at']


class WhatsAppChatSerializer(serializers.ModelSerializer):
    device_name = serializers.ReadOnlyField(source='device.device_name')

    class Meta:
        model = WhatsAppChat
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']