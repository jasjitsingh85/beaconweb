from django.db import models
from sponsored_event import SponsoredEvent
from beaconWeb.apps.beacon.common.constants.push_campaign_type import PUSH_CAMPAIGN_TYPE


class PushCampaignTracker(models.Model):
    event = models.ForeignKey(SponsoredEvent)
    type = models.CharField(max_length=2, choices=PUSH_CAMPAIGN_TYPE.ENUM)
    message = models.CharField(max_length=500)
    total_sent = models.FloatField()
    date_sent = models.DateTimeField("Date Created", auto_now_add=True)

    class Meta:
        app_label = 'beacon'