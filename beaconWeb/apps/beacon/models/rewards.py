from django.db import models
from deal import Deal
from deal_hours import DealHours
from django.contrib.auth.models import User
from beaconWeb.apps.beacon.common.constants.reward_types import REWARD_TYPES


class Rewards(models.Model):
    user = models.ForeignKey(User)
    reward_type = models.CharField(max_length=2, choices=REWARD_TYPES.ENUM, blank=True, null=True)
    deal = models.ForeignKey(Deal, null=True, blank=True)
    reward_value = models.FloatField(null=True, blank=True)
    isRedeemed = models.BooleanField(default=False)

    class Meta:
        app_label = 'beacon'