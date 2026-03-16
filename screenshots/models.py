from django.db import models
from apps.devices.models import Device
import uuid
import os


def screenshot_upload_path(instance, filename):
    """Gera caminho único para cada screenshot"""
    ext = filename.split('.')[-1]
    new_filename = f"{instance.device.device_id}_{instance.timestamp.strftime('%Y%m%d_%H%M%S')}.{ext}"
    return os.path.join('screenshots', new_filename)


class Screenshot(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    device = models.ForeignKey(Device, on_delete=models.CASCADE, related_name='screenshots')
    image = models.ImageField(upload_to=screenshot_upload_path)
    timestamp = models.DateTimeField(auto_now_add=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    file_size = models.IntegerField(default=0)
    is_viewed = models.BooleanField(default=False)

    class Meta:
        ordering = ['-timestamp']
        db_table = 'screenshots'