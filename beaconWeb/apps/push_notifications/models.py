from django.conf import settings
from django.db import models
from gcm.models import AbstractDevice
from gcm.api import send_gcm_message


class AndroidDevice(AbstractDevice):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='android_devices')
    last_notified_at = models.DateTimeField(null=True, blank=True)
    platform = models.CharField(max_length=30, blank=True, null=True)
    display = models.CharField(max_length=30, blank=True, null=True)
    os_version = models.CharField(max_length=20, blank=True, null=True)

    def send_message(self, message=None, title=None):
        data = {}
        if message:
            data['message'] = message
        if title:
            data['title'] = title
        return send_gcm_message(
            api_key=settings.GCM_APIKEY,
            regs_id=[self.reg_id],
            data=data)