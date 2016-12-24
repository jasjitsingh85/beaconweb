from django.db import models
from beaconWeb.common_utils import smart_format


class RawPlace(models.Model):

    city = models.CharField(max_length=128, null=True, blank=True)
    place_description = models.TextField(blank=True, null=True)
    place_type = models.CharField(max_length=128, blank=True, null=True)
    longitude = models.FloatField(db_index=True, blank=True, null=True)
    latitude = models.FloatField(db_index=True, blank=True, null=True)
    name = models.CharField(max_length=128, blank=True, null=True)
    phone = models.CharField(max_length=128, blank=True, null=True)
    street_address = models.CharField(max_length=128, blank=True, null=True)
    website = models.CharField(max_length=128, null=True, blank=True)
    yelp_id = models.CharField(max_length=128, blank=True, null=True, unique=True)
    foursquare_id = models.CharField(max_length=128, blank=True, null=True, unique=True)
    facebook_id = models.CharField(max_length=128, blank=True, null=True, unique=True)
    neighborhood = models.CharField(max_length=150, blank=True, null=True)
    date_updated = models.DateTimeField("Date Updated", auto_now=True)
    date_created = models.DateTimeField("Date Created", auto_now_add=True)

    class Meta:
        app_label = 'beacon'

    def __unicode__(self):
        return smart_format("{0}, {1}", self.name, self.street_address)