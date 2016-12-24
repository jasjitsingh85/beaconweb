from django.db import models
from deal_place import DealPlace
from time import mktime
from beaconWeb.apps.beacon.common.constants.event_type import EVENT_TYPE


class SyndicatedEvents(models.Model):
    title = models.CharField(max_length=500)
    website = models.CharField(max_length=500)
    event_id = models.CharField(max_length=100)
    start = models.DateTimeField()
    end = models.DateTimeField(null=True, blank=True)
    event_type = models.CharField(max_length=2, choices=EVENT_TYPE.ENUM, default=EVENT_TYPE.FACEBOOK)
    place = models.ForeignKey(DealPlace, related_name='event_place')
    date_created = models.DateTimeField("Date Created", auto_now_add=True)
    date_updated = models.DateTimeField("Date Updated", auto_now=True)

    class Meta:
        app_label = 'beacon'

    @property
    def start_time(self):
        return mktime(self.start.timetuple())

    @property
    def web_url(self):
        return "https://www.facebook.com/events/" + str(self.event_id)

    @property
    def deep_link_url(self):
        return "fb://profile/" + str(self.event_id)