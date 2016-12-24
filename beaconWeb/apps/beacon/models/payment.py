from django.db import models
from deal import Deal
from deal_hours import DealHours
from django.contrib.auth.models import User
# from deal_status import DealStatus
from beacon import Beacon
from deal_feedback import Feedback


class Payment(models.Model):
    # deal_status = models.ForeignKey(DealStatus)
    payment_authorization = models.CharField(max_length=20)
    date_submitted = models.DateTimeField("Date Updated", auto_now=True)
    is_submitted = models.BooleanField()

    class Meta:
        app_label = 'beacon'