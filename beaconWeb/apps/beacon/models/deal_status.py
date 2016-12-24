from django.db import models
from deal import Deal
from deal_hours import DealHours
from django.contrib.auth.models import User
from contact import Contact
from beacon import Beacon
from payment import Payment
from deal_feedback import Feedback
from beaconWeb.apps.beacon.common.constants.deal_status import DEAL_STATUS
from beaconWeb.apps.beacon.common.utils.encryption import simple_int_hash
from django.conf import settings
from time import mktime
from beaconWeb.apps.beacon.common.constants.beacon_status_values import BEACON_FOLLOW_STATUS


class DealStatus(models.Model):
    deal = models.ForeignKey(Deal, related_name='deal_statuses')
    deal_status = models.CharField(max_length=10, choices=DEAL_STATUS.ENUM, default=DEAL_STATUS.LOCKED)
    bonus_status = models.CharField(max_length=10, choices=DEAL_STATUS.ENUM, default=DEAL_STATUS.LOCKED)
    beacon = models.ForeignKey(Beacon, related_name='deal_statuses')
    # hours = models.ForeignKey(DealHours, related_name='deal_statuses')
    start = models.DateTimeField()
    end = models.DateTimeField()
    user = models.ForeignKey(User, null=True, blank=True, related_name='deal_statuses')
    contact = models.ForeignKey(Contact, null=True, blank=True, related_name='deal_statuses')
    date_created = models.DateTimeField("Date Created", auto_now_add=True)
    date_updated = models.DateTimeField("Date Updated", auto_now=True)
    saw_invite = models.BooleanField(default=False)
    state = models.CharField(max_length=10, choices=BEACON_FOLLOW_STATUS.ENUM, default=BEACON_FOLLOW_STATUS.INVITED)
    invited_by = models.ForeignKey(User, blank=True, null=True, related_name="deal_sent_invites")
    checked_in_by = models.ForeignKey(User, blank=True, null=True, related_name="deal_check_ins")
    feedback = models.ForeignKey(Feedback, blank=True, null=True)
    image_url = models.CharField(max_length=200, null=True, blank=True)
    payment_authorization = models.CharField(max_length=20, blank=True, null=True)
    isSubmitted = models.BooleanField(default=False)
    public = models.BooleanField(default=True)
    present = models.BooleanField(default=False)
    payment = models.ForeignKey(Payment, null=True, blank=True, related_name="deal_statuses")

    @property
    def deal_url(self):
        return "{0}/deal/{1}/".format(settings.URL, simple_int_hash(self.pk))

    @property
    def conditional_image_url(self):
        if self.image_url != "":
            return self.image_url
        else:
            return self.deal.place.image_url

    @property
    def start_time(self):
        return mktime(self.start.timetuple())

    @property
    def end_time(self):
        return mktime(self.end.timetuple())

    def feedback_boolean(self):
        if self.feedback is None:
            return False
        else:
            return self.feedback.redemption_issue

    class Meta:
        app_label = 'beacon'



