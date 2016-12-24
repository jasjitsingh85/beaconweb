from django.db import models
from beaconWeb.apps.beacon.common.constants.manager_status import MANAGER_STATUS
from market import Market


class EventManager(models.Model):
    name = models.CharField(max_length=100)
    market = models.ForeignKey(Market)
    phone_number = models.CharField(max_length=100)
    email = models.CharField(max_length=100)
    status = models.CharField(max_length=2, choices=MANAGER_STATUS.ENUM)
    active = models.BooleanField(default=True)
    date_created = models.DateTimeField("Date Created", auto_now_add=True)

    class Meta:
        app_label = 'beacon'

    def __unicode__(self):
        return self.name + " in " + self.market.name
