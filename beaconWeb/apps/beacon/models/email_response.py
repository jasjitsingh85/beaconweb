from django.db import models
from beaconWeb.apps.beacon.models.sponsored_event import SponsoredEvent
from beaconWeb.apps.beacon.common.constants.email_status import EMAIL_STATUS
from email_status import EmailStatus


class EmailResponse(models.Model):
    email = models.CharField(max_length=200)
    event = models.ForeignKey(SponsoredEvent, null=True, blank=True)
    response = models.NullBooleanField()
    campaign = models.ForeignKey(EmailStatus, null=True, blank=True)
    status = models.CharField(max_length=2, choices=EMAIL_STATUS.ENUM)
    date_created = models.DateTimeField("Date Created", auto_now_add=True)

    class Meta:
        app_label = 'beacon'