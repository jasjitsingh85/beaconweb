from django.db import models
from market import Market
from sponsored_event import SponsoredEvent
from beaconWeb.apps.beacon.common.constants.email_submission import EMAIL_SUBMISSION


class Emails(models.Model):
    email = models.CharField(max_length=200)
    event = models.ForeignKey(SponsoredEvent, null=True, blank=True)
    market = models.ForeignKey(Market)
    type = models.CharField(max_length=2, choices=EMAIL_SUBMISSION.ENUM, default=EMAIL_SUBMISSION.PAGE)
    date_created = models.DateTimeField("Date Created", auto_now_add=True)

    class Meta:
        app_label = 'beacon'