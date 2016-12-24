from django.db import models
from deal_place import DealPlace
from bitfield import BitField


class SyndicatedDeal(models.Model):
    description = models.TextField()
    start = models.FloatField(blank=True, null=True, default=None)
    end = models.FloatField(blank=True, null=True, default=None)
    days = models.CharField(max_length=7)
    place = models.ForeignKey(DealPlace, related_name='syndicated_deal')
    days_active = BitField(flags=('Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'), blank=True, null=True)
    date_updated = models.DateTimeField("Date Updated", auto_now=True)
    in_review = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)

    class Meta:
        app_label = 'beacon'

    def save(self, *args, **kwargs):
        days = SyndicatedDeal.days_active
        day_bits = [days.Sunday, days.Monday, days.Tuesday, days.Wednesday, days.Thursday, days.Friday, days.Saturday, days.Sunday]
        bitfield = 0
        for i in range(0, 7):
            if self.days[i] == "1":
                bitfield = bitfield | day_bits[i]
        self.days_active = bitfield
        super(SyndicatedDeal, self).save(*args, **kwargs)

    # @property
    # def days(self):
    #     flags = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
    #     bitmask = "".zfill(7)
    #     for i in range(len(flags)):
    #         if getattr(self.days_active, flags[i]).is_set:
    #             bitmask = bitmask[:i] + '1' + bitmask[i+1:]
    #     #        temp fix. first bit dummy to avoid crash on client
    #     return '0' + bitmask