from django.db import models
from sponsored_event import SponsoredEvent


class EventTracker(models.Model):
    event = models.ForeignKey(SponsoredEvent)
    attendee_count = models.PositiveIntegerField()
    interested_count = models.PositiveIntegerField()
    date_created = models.DateTimeField("Date Created", auto_now_add=True)

    class Meta:
        app_label = 'beacon'