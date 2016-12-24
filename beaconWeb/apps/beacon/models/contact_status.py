from django.db import models
from beaconWeb.apps.beacon.common.constants.contact_status import CONTACT_STATUS
from deal_status import DealStatus
from contact import Contact
from django.contrib.auth.models import User


class ContactStatus(models.Model):
    deal_status = models.ForeignKey(DealStatus, blank=True, null=True)
    contact = models.ForeignKey(Contact, blank=True, null=True)
    referring_user = models.ForeignKey(User, blank=True, null=True)
    referred_phone_number = models.CharField(max_length=20, blank=True, null=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    sms_response = models.CharField(max_length=1, choices=CONTACT_STATUS.ENUM, blank=True, null=True, default=None)
    link_clicked = models.BooleanField(default=False)
    installed_app = models.BooleanField(default=False)
    date_created = models.DateTimeField("Date Created", auto_now_add=True)
    second_sms_sent = models.BooleanField(default=False)

    class Meta:
        app_label = 'beacon'



