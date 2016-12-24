from django.db import models
from django.contrib.auth.models import User
from beaconWeb.common_utils import smart_format
from beaconWeb.apps.beacon.models.beacon import Beacon
from beaconWeb.apps.beacon.models.contact import Contact
from beaconWeb.apps.beacon.common.constants.beacon_status_values import BEACON_FOLLOW_STATUS


class BeaconFollow(models.Model):
    user = models.ForeignKey(User, blank=True, null=True, related_name='received_invites')
    checked_in_by = models.ForeignKey(User, blank=True, null=True, related_name="check_ins")
    contact = models.ForeignKey(Contact, blank=True, null=True)
    beacon = models.ForeignKey(Beacon, related_name="beacon_follows")
    invited_by = models.ForeignKey(User, blank=True, null=True, related_name="sent_invites")
    state = models.CharField(max_length=10, choices=BEACON_FOLLOW_STATUS.ENUM, default=BEACON_FOLLOW_STATUS.INVITED)
    date_created = models.DateTimeField("Date Created", auto_now_add=True)
    date_updated = models.DateTimeField("Date Updated", auto_now=True)
    saw_invite = models.BooleanField(default=False)

    class Meta:
        app_label = 'beacon'

    def __unicode__(self):
        if self.user:
            return smart_format("{0} -> {1}", self.beacon.description, self.user.first_name)
        else:
            return smart_format("{0} -> {1}", self.beacon.description, self.contact.name)