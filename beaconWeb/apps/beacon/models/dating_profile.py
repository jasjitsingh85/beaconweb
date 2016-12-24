from django.db import models
from beaconWeb.apps.beacon.common.constants.gender_values import GENDER_VALUE
from beaconWeb.apps.beacon.models.profile import Profile


class DatingProfile(models.Model):
    dating_profile = models.OneToOneField(Profile)
    user_gender = models.CharField(max_length=1, choices=GENDER_VALUE.ENUM, blank=True, null=True, default=None)
    preference = models.CharField(max_length=1, choices=GENDER_VALUE.ENUM, blank=True, null=True, default=None)
    image_url = models.CharField(null=True, blank=True, max_length=500)
    age = models.PositiveIntegerField(null=True, blank=True)
    has_setup = models.BooleanField(default=False)
    date_updated = models.DateTimeField("Date Updated", auto_now=True)
    date_created = models.DateTimeField("Date Created", auto_now_add=True)

    class Meta:
        app_label = 'beacon'
