from django.db import models
from deal_place import DealPlace
from beaconWeb.apps.beacon.common.constants.place_contact_type import PLACE_CONTACT_TYPE


class PlaceContact(models.Model):
    name = models.CharField(max_length=200, null=True, blank=True)
    place = models.ForeignKey(DealPlace)
    email = models.CharField(max_length=255)
    priority = models.BooleanField(default=False)
    phone = models.CharField(max_length=20, blank=True, null=True)
    responded = models.BooleanField(default=False)
    emails_received = models.IntegerField(default=0)
    type = models.CharField(max_length=10, choices=PLACE_CONTACT_TYPE.ENUM, blank=True, null=True)

    class Meta:
        app_label = 'beacon'

    def __unicode__(self):
        return self.email