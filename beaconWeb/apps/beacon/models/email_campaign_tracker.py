from django.db import models
from sponsored_event import SponsoredEvent
from emails import Emails
from cash_payment import CashPayment
from beaconWeb.apps.beacon.common.constants.email_campaign_type import EMAIL_CAMPAIGN_TYPE
from django.contrib.auth.models import User


class EmailCampaignTracker(models.Model):
    event = models.ForeignKey(SponsoredEvent)
    type = models.CharField(max_length=2, choices=EMAIL_CAMPAIGN_TYPE.ENUM)
    user = models.ForeignKey(User, blank=True, null=True)
    email = models.ForeignKey(Emails, blank=True, null=True)
    cash_payment = models.ForeignKey(CashPayment, blank=True, null=True)
    subject = models.CharField(max_length=500)
    description = models.CharField(max_length=5000)
    total_sent = models.FloatField()
    category = models.CharField(max_length=500)
    date_sent = models.DateTimeField("Date Created", auto_now_add=True)

    class Meta:
        app_label = 'beacon'