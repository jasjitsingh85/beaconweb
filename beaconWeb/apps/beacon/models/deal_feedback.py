from django.db import models
from beaconWeb.common_utils import smart_format


class Feedback(models.Model):
    redemption_issue = models.BooleanField(default=False)
    date_created = models.DateTimeField("Date Created", auto_now_add=True)

    class Meta:
        app_label = 'beacon'

    def __unicode__(self):
        return smart_format("{0}->{1}", self.deal_status.user.first_name, self.deal_status.deal.place.name)
