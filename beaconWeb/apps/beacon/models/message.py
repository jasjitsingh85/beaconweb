from django.db import models
from django.contrib.auth.models import User
from beaconWeb.apps.beacon.models.sponsored_event import SponsoredEvent
from time import mktime


class Message(models.Model):
    user = models.ForeignKey(User, blank=True, null=True)
    event = models.ForeignKey(SponsoredEvent, blank=True, null=True)
    message = models.CharField(max_length=500, blank=True, null=True)
    image_url = models.CharField(max_length=500, blank=True, null=True)
    date_created = models.DateTimeField("Date Created", auto_now_add=True)

    class Meta:
        app_label = 'beacon'

    @property
    def message_time(self):
        return mktime(self.date_created.timetuple())
