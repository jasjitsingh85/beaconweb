from django.db import models
from django.contrib.auth.models import User
from beaconWeb.apps.beacon.common.constants.gender_values import GENDER_VALUE
from rest_framework.authtoken.models import Token
from ios_notifications.models import Device
from beaconWeb.apps.beacon.common.constants.user_type import USER_TYPE
from beaconWeb.apps.beacon.models.deal_place import DealPlace
from beaconWeb.apps.beacon.models.rewards import Rewards
from beaconWeb.apps.beacon.models.reward_item import RewardItem
from beaconWeb.apps.beacon.models.promo import Promo
from beaconWeb.apps.beacon.common.constants.reward_types import REWARD_TYPES


class Profile(models.Model):
    user = models.OneToOneField(User)
    phone_number = models.CharField(max_length=20, null=True, blank=True)
    normalized_phone = models.CharField(max_length=20, db_index=True, null=True, blank=True)
    activated = models.BooleanField(default=False)
    activation_code = models.CharField(max_length=5, null=True, blank=True)
    gender = models.CharField(max_length=1, choices=GENDER_VALUE.ENUM, null=True, blank=True)
    user_type = models.CharField(max_length=2, choices=USER_TYPE.ENUM, default=USER_TYPE.HOTSPOT)
    deal_place = models.ForeignKey(DealPlace, null=True, blank=True)
    date_updated = models.DateTimeField("Date Updated", auto_now=True)
    feed_updated = models.DateTimeField(null=True, blank=True)
    facebook_id = models.CharField(max_length=100, null=True, blank=True)
    used_promo_code = models.CharField(max_length=100, null=True, blank=True)
    fb_token = models.CharField(max_length=400, null=True, blank=True)
    is_underage = models.BooleanField(default=False)
    date_contacted_for_interview = models.DateTimeField(null=True, blank=True)
    date_of_interview = models.DateTimeField(null=True, blank=True)

    class Meta:
        app_label = 'beacon'

    def __unicode__(self):
        return self.user.first_name

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.normalized_phone == other.normalized_phone

    @property
    def avatar_url(self):
        index = (self.user.id % 12) + 1
        url = "https://s3.amazonaws.com/hotspot-avatars/{0}.png".format(index)
        return url

    @property
    def token(self):
        if Token.objects.filter(user=self.user).exists():
            return Token.objects.get(user=self.user).key

    @property
    def devices_tokens(self):
        return Device.objects.filter(users__id__in=[self.user.pk])

    @property
    def reward_score(self):
        rewards = Rewards.objects.filter(user=self.user).exclude(reward_value=None).values_list('reward_value', flat=True)
        return int(sum(rewards))

    @property
    def number_of_reward_items(self):
        reward_items = RewardItem.objects.filter(user=self.user, reward_type=REWARD_TYPES.DRINK, isRedeemed=False)
        return len(reward_items)

    @property
    def promo_code(self):
        if Promo.objects.filter(referring_user=self.user, item_number=1).exists():
            promo_object = Promo.objects.filter(referring_user=self.user, item_number=1)[0]
            return promo_object.promo_code
        else:
            return ""

