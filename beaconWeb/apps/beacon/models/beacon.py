from django.db import models
from django.contrib.auth.models import User
from deal_place import DealPlace
from time import mktime
from beaconWeb.common_utils import smart_format


class Beacon(models.Model):
    creator = models.ForeignKey(User, related_name='created_hotspots')
    place = models.ForeignKey(DealPlace)
    description = models.CharField(max_length=255)
    address = models.CharField(max_length=255)
    time = models.DateTimeField("Beacon Time")
    cancelled = models.BooleanField(default=False)
    private = models.BooleanField(default=False)
    longitude = models.FloatField(db_index=True)
    latitude = models.FloatField(db_index=True)
    facebook_place_id = models.BigIntegerField(blank=True, null=True)
    date_created = models.DateTimeField("Date Created", auto_now_add=True)
    date_updated = models.DateTimeField("Date Updated", auto_now=True)
    isActivated = models.BooleanField(default=True)
    custom_deal_message = models.TextField(blank=True, null=True)

    class Meta:
        app_label = 'beacon'

    def __unicode__(self):
        return smart_format("{0}->{1}", self.creator, self.description)

    @property
    def beacon_time(self):
        return mktime(self.time.timetuple())