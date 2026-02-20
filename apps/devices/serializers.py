from rest_framework import serializers
from .models import Device, DeviceLog


class DeviceSerializer(serializers.ModelSerializer):
    user_email = serializers.ReadOnlyField(source='user.email')

    class Meta:
        model = Device
        fields = [
            'id', 'device_id', 'device_name', 'device_model', 'manufacturer',
            'os_type', 'os_version', 'app_version', 'phone_number', 'imei',
            'status', 'user', 'user_email', 'assigned_to', 'last_sync',
            'created_at', 'updated_at', 'battery_level', 'storage_used',
            'is_rooted'
        ]
        read_only_fields = ['id', 'user', 'last_sync', 'created_at', 'updated_at']

    def validate_device_id(self, value):
        """Ensure device_id is unique per user"""
        user = self.context['request'].user
        if Device.objects.filter(device_id=value, user=user).exists():
            if self.instance and self.instance.device_id == value:
                return value
            raise serializers.ValidationError("Este dispositivo já está registrado para este usuário.")
        return value


class DeviceLogSerializer(serializers.ModelSerializer):
    device_name = serializers.ReadOnlyField(source='device.device_name')

    class Meta:
        model = DeviceLog
        fields = ['id', 'device', 'device_name', 'log_type', 'message', 'details', 'created_at']
        read_only_fields = ['id', 'created_at']


class DeviceStatusSerializer(serializers.Serializer):
    """Serializer for device status updates"""
    status = serializers.ChoiceField(choices=['active', 'inactive', 'blocked', 'maintenance'])
    reason = serializers.CharField(required=False, allow_blank=True)


class DeviceSyncSerializer(serializers.Serializer):
    """Serializer for device sync request"""
    device_id = serializers.CharField(required=True)
    last_sync = serializers.DateTimeField(required=False)


class DeviceBulkActionSerializer(serializers.Serializer):
    """Serializer for bulk actions on devices"""
    device_ids = serializers.ListField(
        child=serializers.UUIDField(),
        allow_empty=False
    )
    action = serializers.ChoiceField(choices=['block', 'unblock', 'delete', 'sync'])