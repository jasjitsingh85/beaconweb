from django.db import models
from django.contrib.auth.models import User
from beaconWeb.apps.beacon.models.sponsored_event import SponsoredEvent
from beaconWeb.common_utils import smart_format


class UserFeedback(models.Model):
    user = models.ForeignKey(User)
    sponsored_event = models.ForeignKey(SponsoredEvent)
    nps_score = models.IntegerField()
    description = models.TextField(null=True, blank=True)
    date_updated = models.DateTimeField("Date Updated", auto_now=True)
    date_created = models.DateTimeField("Date Created", auto_now_add=True)
    question1 = models.TextField(null=True, blank=True)
    question2 = models.TextField(null=True, blank=True)
    question3 = models.TextField(null=True, blank=True)
    question4 = models.TextField(null=True, blank=True)

    class Meta:
        app_label = 'beacon'

    def __unicode__(self):
        return smart_format("{0}, {1}", self.user.first_name, self.nps_score)
