from django.db import models
from event_manager import EventManager
from sponsored_event import SponsoredEvent
from beaconWeb.apps.beacon.common.constants.staffer_status import STAFFER_STATUS


class EventStaffer(models.Model):
    manager = models.ForeignKey(EventManager)
    event = models.ForeignKey(SponsoredEvent)
    # general_manager = models.ForeignKey(User)
    is_staffed = models.BooleanField(default=True)
    status = models.CharField(max_length=2, choices=STAFFER_STATUS.ENUM, null=True, blank=True)
    date_created = models.DateTimeField("Date Created", auto_now_add=True)

    class Meta:
        app_label = 'beacon'

    def __unicode__(self):
        return "{0} at {1} ".format(self.manager.name, self.event.place.name)