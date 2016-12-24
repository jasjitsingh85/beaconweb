from django.db import models
from django.contrib.auth.models import User
from deal_place import DealPlace
from beaconWeb.apps.beacon.common.constants.region_state import REGION_STATE
from beaconWeb.apps.beacon.common.constants.region_monitoring import REGION_TYPE


class RegionState(models.Model):
    user = models.ForeignKey(User, related_name='region_states')
    region_type = models.CharField(max_length=20, choices=REGION_TYPE.ENUM, default=REGION_TYPE.IBEACON)
    region_state = models.CharField(max_length=20, choices=REGION_STATE.ENUM, default=REGION_STATE.ENTER)
    place = models.ForeignKey(DealPlace, related_name='region_states')
    showed_notification = models.BooleanField(default=False)
    date_created = models.DateTimeField("Date Created", auto_now_add=True)


    class Meta:
        app_label = 'beacon'