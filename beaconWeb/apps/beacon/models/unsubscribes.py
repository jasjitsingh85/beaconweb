from django.db import models
from beaconWeb.apps.beacon.common.constants.email_status import EMAIL_STATUS


class Unsubscribe(models.Model):
    email = models.CharField(max_length=200)
    status = models.CharField(max_length=2, choices=EMAIL_STATUS.ENUM, default=EMAIL_STATUS.UNSUBSCRIBE)
    date_created = models.DateTimeField("Date Created", auto_now_add=True)

    class Meta:
        app_label = 'beacon'