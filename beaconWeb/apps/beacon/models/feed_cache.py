from django.db import models
from deal_place import DealPlace
from beaconWeb.apps.beacon.common.constants.social_sources import SOCIAL_SOURCE


class FeedCache(models.Model):
    place = models.ForeignKey(DealPlace)
    message = models.CharField(max_length=100000, null=True, blank=True)
    image_url = models.CharField(max_length=10000, null=True, blank=True)
    content_id = models.CharField(max_length=1000, null=True, blank=True)
    source = models.CharField(max_length=10, choices=SOCIAL_SOURCE.ENUM, null=True, blank=True)
    date_created = models.DateTimeField()
    date_updated = models.DateTimeField("Date Updated", auto_now=True)

    class Meta:
        app_label = 'beacon'