from django.db import models
from bitfield import BitField
from deal import Deal
from beaconWeb.common_utils import smart_format


class DealHours(models.Model):
    deal = models.ForeignKey(Deal, related_name='hours')
    start = models.FloatField()
    end = models.FloatField()
    open_hours = models.BooleanField(default=False)
    days_active = BitField(flags=('Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'))
    event_date = models.DateTimeField(null=True, blank=True)

    class Meta:
        app_label = 'beacon'

    def __unicode__(self):
        return smart_format("{0} {1}, {2}-{3}", self.deal.place, self.days, time_string(self.start), time_string(self.end))

    @property
    def days(self):
        flags = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
        bitmask = "".zfill(7)
        for i in range(len(flags)):
            if getattr(self.days_active, flags[i]).is_set:
                bitmask = bitmask[:i] + '1' + bitmask[i+1:]
        #        temp fix. first bit dummy to avoid crash on client
        return '0' + bitmask


def time_string(seconds):
        hour = int(seconds/(60*60))
        minutes = int((seconds - hour*60*60)/60)
        return "{0}:{1:02}".format(hour, minutes)

