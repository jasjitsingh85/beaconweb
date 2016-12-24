from django.db import models
from deal_place import DealPlace
from beaconWeb.common_utils import smart_format
from time import mktime
from django.conf import settings
from beaconWeb.apps.beacon.common.utils.encryption import simple_int_hash
from market import Market
import pytz


class SponsoredEvent(models.Model):
    place = models.ForeignKey(DealPlace, null=True, blank=True)
    title = models.TextField(null=True, blank=True)
    description = models.CharField(max_length=5000, null=True, blank=True)
    active = models.BooleanField(default=True)
    item_name = models.CharField(max_length=100, null=True, blank=True)
    item_cost = models.FloatField(null=True, blank=True)
    item_price = models.FloatField(null=True, blank=True)
    presale_item_price = models.FloatField(null=True, blank=True)
    web_item_price = models.FloatField()
    capacity = models.PositiveIntegerField(null=True, blank=True)
    presale_cap = models.PositiveIntegerField(null=True, blank=True)
    facebook_event_id = models.CharField(max_length=100)
    facebook_campaign_id = models.CharField(max_length=100, null=True, blank=True)
    start = models.DateTimeField()
    end = models.DateTimeField()
    market = models.ForeignKey(Market, null=True, blank=True)
    chat_channel_url = models.CharField(max_length=100)
    date_created = models.DateTimeField("Date Created", auto_now_add=True)
    date_updated = models.DateTimeField("Date Updated", auto_now=True)

    class Meta:
        app_label = 'beacon'

    def __unicode__(self):
        return smart_format("{0}:{1}", self.place, self.title)

    @property
    def start_time(self):
        return mktime(self.start.timetuple())

    @property
    def end_time(self):
        return mktime(self.end.timetuple())

    @property
    def web_url(self):
        return "https://www.facebook.com/events/" + str(self.facebook_event_id)

    @property
    def deep_link_url(self):
        return "fb://profile/" + str(self.facebook_event_id)

    @property
    def ticket_link_url(self):
        return "{0}/tickets/{1}".format(settings.URL, simple_int_hash(self.id))

    @property
    def timezone_adjusted_start(self):
        new_timezone = pytz.timezone(self.market.timezone_id)
        server_timezone = pytz.timezone(settings.TIME_ZONE)
        localized_start_time = server_timezone.localize(self.start)
        return localized_start_time.astimezone(tz=new_timezone)

    @property
    def timezone_adjusted_end(self):
        new_timezone = pytz.timezone(self.market.timezone_id)
        server_timezone = pytz.timezone(settings.TIME_ZONE)
        localized_end_time = server_timezone.localize(self.end)
        return localized_end_time.astimezone(tz=new_timezone)
