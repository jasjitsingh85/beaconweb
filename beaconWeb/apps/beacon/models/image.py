from django.db import models
from django.contrib.auth.models import User
from beaconWeb.apps.beacon.models.beacon import Beacon


class Image(models.Model):
    image_key = models.CharField(max_length=60)
    beacon = models.ForeignKey(Beacon, null=True, blank=True)
    user = models.ForeignKey(User)
    date_created = models.DateTimeField("Date Created", auto_now_add=True)

    class Meta:
        app_label = 'beacon'