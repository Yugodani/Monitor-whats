from rest_framework import serializers
from .models import Screenshot


class ScreenshotSerializer(serializers.ModelSerializer):
    device_name = serializers.ReadOnlyField(source='device.device_name')
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = Screenshot
        fields = '__all__'

    def get_image_url(self, obj):
        request = self.context.get('request')
        if obj.image and request:
            return request.build_absolute_uri(obj.image.url)
        return None