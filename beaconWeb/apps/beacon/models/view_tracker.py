from django.db import models
from django.contrib.auth.models import User
from beaconWeb.apps.beacon.common.constants.view_types import VIEW_TYPE


class ViewTracker(models.Model):
    user = models.ForeignKey(User, null=True, blank=True)
    view_id = models.PositiveIntegerField(null=True, blank=True)
    view_type = models.CharField(max_length=50, choices=VIEW_TYPE.ENUM)
    date_created = models.DateTimeField("Date Created", auto_now_add=True)

    class Meta:
        app_label = 'beacon'