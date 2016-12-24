from django.db import models
from sponsored_event import SponsoredEvent
from beaconWeb.apps.beacon.common.constants.event_status import EVENT_STATUS


class CashPayment(models.Model):
    event = models.ForeignKey(SponsoredEvent)
    total = models.FloatField()
    tip = models.FloatField(null=True, blank=True)
    attendees = models.PositiveIntegerField()
    promo_code = models.CharField(max_length=100, null=True, blank=True)
    name = models.CharField(max_length=100, null=True, blank=True)
    email = models.CharField(max_length=100, null=True, blank=True)
    status = models.CharField(max_length=10, choices=EVENT_STATUS.ENUM, default=EVENT_STATUS.GOING)
    date_created = models.DateTimeField("Date Created", auto_now_add=True)

    class Meta:
        app_label = 'beacon'
