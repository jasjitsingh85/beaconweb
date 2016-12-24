from django.db import models
from sponsored_event import SponsoredEvent
from django.contrib.auth.models import User
from payment import Payment
from beaconWeb.apps.beacon.common.constants.event_status import EVENT_STATUS


class EventStatus(models.Model):
    event = models.ForeignKey(SponsoredEvent, related_name='event_statuses')
    status = models.CharField(max_length=10, choices=EVENT_STATUS.ENUM, default=EVENT_STATUS.GOING)
    user = models.ForeignKey(User, null=True, blank=True, related_name='event_statuses')
    date_created = models.DateTimeField("Date Created", auto_now_add=True)
    date_updated = models.DateTimeField("Date Updated", auto_now=True)
    image_url = models.CharField(max_length=200, null=True, blank=True)
    payment_authorization = models.CharField(max_length=20, blank=True, null=True)
    is_submitted = models.BooleanField(default=False)
    public = models.BooleanField(default=True)
    present = models.BooleanField(default=False)
    welcome_message_sent = models.BooleanField(default=False)
    arrival_message_sent = models.BooleanField(default=False)
    payment = models.ForeignKey(Payment, null=True, blank=True, related_name="event_statuses")
    tip_amount = models.FloatField(default=0, null=True, blank=True)
    is_presale = models.BooleanField()
    refund_authorization = models.CharField(max_length=20, null=True, blank=True)

    class Meta:
        app_label = 'beacon'

