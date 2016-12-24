from django.db import models
from event_manager import EventManager
from sponsored_event import SponsoredEvent
from beaconWeb.apps.beacon.common.constants.staffer_notification import STAFFER_NOTIFICATION
from beaconWeb.apps.beacon.common.constants.staffer_response import STAFFER_RESPONSE


class StafferNotification(models.Model):
    manager = models.ForeignKey(EventManager)
    event = models.ForeignKey(SponsoredEvent)
    notification_type = models.CharField(max_length=2, choices=STAFFER_NOTIFICATION.ENUM)
    response = models.CharField(max_length=2, choices=STAFFER_RESPONSE.ENUM, null=True, blank=True)
    date_created = models.DateTimeField("Date Created", auto_now_add=True)
    date_updated = models.DateTimeField("Date Updated", auto_now=True)

    class Meta:
        app_label = 'beacon'