from django.db import models
from deal_place import DealPlace
from beaconWeb.common_utils import smart_format
from beaconWeb.apps.beacon.common.constants.deal_type import DEAL_TYPE


class Deal(models.Model):
    place = models.ForeignKey(DealPlace)
    deal_description = models.TextField()
    deal_description_short = models.TextField(null=True, blank=True)
    additional_info = models.TextField(null=True, blank=True)
    invite_requirement = models.IntegerField()
    bonus_description = models.TextField(null=True, blank=True)
    bonus_description_short = models.TextField(null=True, blank=True)
    bonus_invite_requirement = models.IntegerField(null=True, blank=True)
    notification_text = models.TextField()
    invite_description = models.TextField()
    invite_prompt = models.TextField()
    active = models.BooleanField(default=True)
    deal_type = models.CharField(max_length=2, choices=DEAL_TYPE.ENUM, default=DEAL_TYPE.DEFAULT)
    in_app_payment = models.BooleanField(default=False)
    item_name = models.CharField(max_length=100, null=True, blank=True)
    item_cost = models.FloatField(null=True, blank=True)
    item_price = models.FloatField(null=True, blank=True)
    item_market_price = models.FloatField(null=True, blank=True)
    date_created = models.DateTimeField("Date Created", auto_now_add=True)
    date_updated = models.DateTimeField("Date Updated", auto_now=True)
    reward_eligibility = models.BooleanField(default=False)
    pos_item_id = models.CharField(max_length=128, blank=True, null=True)
    pos_price_id = models.CharField(max_length=128, blank=True, null=True)
    recently_added = models.BooleanField(default=True)

    @property
    def item_point_cost(self):
        return 0

    class Meta:
        app_label = 'beacon'

    def __unicode__(self):
        return smart_format("{0}:{1}", self.place, self.deal_description)