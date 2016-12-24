from django.db import models
from sponsored_event import SponsoredEvent


class EventHours(models.Model):
    event = models.ForeignKey(SponsoredEvent, related_name='hours')
    event_start = models.DateTimeField()
    event_end = models.DateTimeField()

    class Meta:
        app_label = 'beacon'

