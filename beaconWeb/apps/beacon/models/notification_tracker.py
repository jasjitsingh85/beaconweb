from django.db import models
from django.contrib.auth.models import User
from beaconWeb.apps.beacon.common.constants.notification_types import NOTIFICATION_TYPE
from sponsored_event import SponsoredEvent


class NotificationTracker(models.Model):
    recipient = models.ForeignKey(User, null=True, blank=True, related_name='receiving_user')
    sender = models.ForeignKey(User, null=True, blank=True, related_name='sending_user')
    event = models.ForeignKey(SponsoredEvent, null=True, blank=True)
    notification_detail = models.CharField(max_length=1000, null=True, blank=True)
    notification_type = models.CharField(max_length=50, choices=NOTIFICATION_TYPE.ENUM)
    date_created = models.DateTimeField("Date Created", auto_now_add=True)

    class Meta:
        app_label = 'beacon'