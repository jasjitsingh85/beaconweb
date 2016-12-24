from django.db import models
from django.contrib.auth.models import User
from beaconWeb.common_utils import smart_format
from beaconWeb.apps.beacon.classes.foursquare_client import FoursquareClient
from raven.contrib.django.models import client as raven_client

class Recommendation(models.Model):
    user = models.ForeignKey(User, related_name='recommendations')
    foursquare_venue_id = models.CharField(max_length=255, null=True)
    message_text = models.CharField(max_length=256)
    date_created = models.DateTimeField("Date Created", auto_now_add=True)

    class Meta:
        app_label = 'beacon'

    def __unicode__(self):
        return smart_format("{0}:{1}", self.user, self.message_text)

    def load_extra_properties(self):
        client = FoursquareClient.shared_client
        try:
            venue_data = client.venues(self.foursquare_venue_id)['venue']
            self.location = venue_data['location']
            self.venue_name = venue_data['name']
        except:
            raven_client.captureException()






