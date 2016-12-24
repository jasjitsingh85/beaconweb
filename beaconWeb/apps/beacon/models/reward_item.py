from django.db import models
from django.contrib.auth.models import User
from beaconWeb.apps.beacon.common.constants.reward_types import REWARD_TYPES


class RewardItem(models.Model):
    user = models.ForeignKey(User)
    reward_type = models.CharField(max_length=2, choices=REWARD_TYPES.ENUM, default=REWARD_TYPES.DRINK, blank=True, null=True)
    isRedeemed = models.BooleanField(default=False)
    promo_code = models.CharField(max_length=50, null=True, blank=True)
    date_created = models.DateTimeField("Date Created", auto_now_add=True)
    date_updated = models.DateTimeField("Date Updated", auto_now=True)
    date_expired = models.DateTimeField(null=True, blank=True)

    class Meta:
        app_label = 'beacon'