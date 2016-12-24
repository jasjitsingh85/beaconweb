from django.db import models
from beaconWeb.apps.beacon.common.constants.display_locations import DISPLAY_LOCATIONS


class ContentOption(models.Model):
    content_option = models.CharField(max_length=255)
    display_location = models.CharField(max_length=2, choices=DISPLAY_LOCATIONS.ENUM)

    class Meta:
        app_label = 'beacon'

    def __unicode__(self):
        return "{0}".format(self.content_option)