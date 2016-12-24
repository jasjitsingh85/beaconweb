from django.db import models
from sponsored_event import SponsoredEvent


class WebPromo(models.Model):
    event = models.ForeignKey(SponsoredEvent)
    code = models.CharField(max_length=100)
    price = models.FloatField(null=True, blank=True)
    content = models.CharField(max_length=1000, null=True, blank=True)
    attendee_limit = models.PositiveSmallIntegerField(null=True, blank=True)
    is_used = models.NullBooleanField()
    date_created = models.DateTimeField("Date Created", auto_now_add=True)

    class Meta:
        app_label = 'beacon'