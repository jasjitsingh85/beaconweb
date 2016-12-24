from django.db import models
from beaconWeb.common_utils import smart_format
from beaconWeb.apps.beacon.common.constants.place_sales_status import PLACE_SALES_STATUS
from point_of_sale import PointOfSale


class DealPlace(models.Model):
    longitude = models.FloatField(db_index=True)
    latitude = models.FloatField(db_index=True)
    name = models.CharField(max_length=128)
    street_address = models.CharField(max_length=128)
    phone = models.CharField(max_length=20, blank=True, null=True)
    source_image_url = models.CharField(max_length=400, blank=True, null=True)
    # image_url = models.CharField(max_length=400, blank=True, null=True)
    yelp_id = models.CharField(max_length=128, blank=True, null=True)
    yelp_rating_image_url = models.CharField(max_length=256, blank=True, null=True)
    yelp_review_count = models.IntegerField(blank=True, null=True)
    foursquare_id = models.CharField(max_length=128, blank=True, null=True)
    facebook_id = models.CharField(max_length=128, blank=True, null=True)
    instagram_id = models.CharField(max_length=128, blank=True, null=True)
    twitter_id = models.CharField(max_length=128, blank=True, null=True)
    place_description = models.TextField(blank=True, null=True)
    place_type = models.CharField(max_length=150, blank=True, null=True)
    neighborhood = models.CharField(max_length=150, blank=True, null=True)
    email = models.CharField(max_length=40, blank=True, null=True)
    website = models.CharField(max_length=500, blank=True, null=True)
    events_url = models.CharField(max_length=250, blank=True, null=True)
    closed = models.BooleanField(default=False)
    date_updated = models.DateTimeField("Date Updated", auto_now=True)
    in_review = models.BooleanField(default=False)
    pipeline_status = models.CharField(max_length=10, choices=PLACE_SALES_STATUS.ENUM, blank=True, null=True)
    point_of_sale = models.OneToOneField(PointOfSale, blank=True, null=True)

    class Meta:
        app_label = 'beacon'

    def __unicode__(self):
        return smart_format("{0}, {1}", self.name, self.street_address)

    @property
    def image_url(self):
        if self.source_image_url:
            return self.source_image_url
        else:
            index = (self.id % 9) + 1
            url = "https://s3-us-west-2.amazonaws.com/hotspot-venue-images/placeholder{0}.png".format(index)
            return url

    @property
    def has_pos(self):
        if self.point_of_sale:
            return True
        else:
            return False
