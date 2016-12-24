from django.db import models
from beaconWeb.apps.beacon.models.dating_profile import DatingProfile
from beaconWeb.apps.beacon.models.sponsored_event import SponsoredEvent


class DatingMatch(models.Model):
    dating_profile_selector = models.ForeignKey(DatingProfile, related_name='dating_selector')
    dating_profile_selectee = models.ForeignKey(DatingProfile, related_name='dating_selectee')
    event = models.ForeignKey(SponsoredEvent)
    is_selected = models.BooleanField()
    date_created = models.DateTimeField("Date Created", auto_now_add=True)

    class Meta:
        app_label = 'beacon'
