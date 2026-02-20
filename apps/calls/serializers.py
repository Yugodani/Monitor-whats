from rest_framework import serializers
from .models import Call
from apps.devices.models import Device


class CallSerializer(serializers.ModelSerializer):
    device_name = serializers.ReadOnlyField(source='device.device_name')
    contact_display = serializers.SerializerMethodField()

    class Meta:
        model = Call
        fields = [
            'id', 'device', 'device_name', 'phone_number', 'contact_name',
            'contact_display', 'call_type', 'duration', 'call_date',
            'synced_at', 'sim_slot', 'imei', 'location', 'is_deleted',
            'deleted_at'
        ]
        read_only_fields = ['id', 'synced_at']

    def get_contact_display(self, obj):
        """Return contact name if available, otherwise phone number"""
        return obj.contact_name or obj.phone_number

    def validate_device(self, value):
        """Ensure device belongs to the user"""
        user = self.context['request'].user
        if value.user != user:
            raise serializers.ValidationError("Dispositivo não pertence ao usuário.")
        return value


class CallBulkSyncSerializer(serializers.Serializer):
    """Serializer for bulk syncing calls from mobile"""
    device_id = serializers.CharField(required=True)
    calls = serializers.ListField(
        child=serializers.DictField(),
        required=True
    )

    def validate_device_id(self, value):
        """Validate device exists and belongs to user"""
        user = self.context['request'].user
        try:
            device = Device.objects.get(device_id=value, user=user)
        except Device.DoesNotExist:
            raise serializers.ValidationError("Dispositivo não encontrado.")
        return device


class CallStatisticsSerializer(serializers.Serializer):
    """Serializer for call statistics response"""
    total_calls = serializers.IntegerField()
    total_duration = serializers.IntegerField()
    average_duration = serializers.FloatField()
    by_type = serializers.ListField(child=serializers.DictField())
    by_day = serializers.ListField(child=serializers.DictField())
    top_numbers = serializers.ListField(child=serializers.DictField())


class CallExportSerializer(serializers.Serializer):
    """Serializer for call export options"""
    format = serializers.ChoiceField(choices=['csv', 'excel', 'pdf'])
    start_date = serializers.DateField(required=False)
    end_date = serializers.DateField(required=False)
    device_id = serializers.UUIDField(required=False)
    include_deleted = serializers.BooleanField(default=False)