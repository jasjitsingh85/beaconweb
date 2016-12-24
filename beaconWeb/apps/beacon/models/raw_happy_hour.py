from django.db import models
from beaconWeb.apps.beacon.models.deal_place import DealPlace
from beaconWeb.common_utils import smart_format


class RawHappyHour(models.Model):
    gt_id = models.IntegerField(unique=True, blank=True, null=True)
    place = models.ForeignKey(DealPlace, blank=True, null=True)
    city = models.CharField(max_length=500, null=True, blank=True)
    company_description = models.TextField(blank=True, null=True)
    cuisine_label = models.CharField(max_length=500, blank=True, null=True)
    longitude = models.FloatField(db_index=True, blank=True, null=True)
    latitude = models.FloatField(db_index=True, blank=True, null=True)
    name = models.CharField(max_length=500, blank=True, null=True)
    phone = models.CharField(max_length=500, blank=True, null=True)
    street = models.CharField(max_length=500, blank=True, null=True)
    website = models.CharField(max_length=500, null=True, blank=True)
    days = models.CharField(max_length=500, blank=True, null=True)
    start_time = models.CharField(max_length=500, blank=True, null=True)
    end_time = models.CharField(max_length=500, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    active = models.BooleanField(default=True)
    date_updated = models.DateTimeField("Date Updated", auto_now=True)
    date_created = models.DateTimeField("Date Created", auto_now_add=True)

    class Meta:
        app_label = 'beacon'

    def __unicode__(self):
        return smart_format("{0}, {1}", self.name, self.street)