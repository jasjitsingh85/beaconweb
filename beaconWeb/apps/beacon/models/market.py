from django.db import models


class Market(models.Model):
    name = models.CharField(max_length=100)
    latitude = models.FloatField(db_index=True)
    longitude = models.FloatField(db_index=True)
    timezone_id = models.CharField(max_length=100, null=True, blank=True)
    date_created = models.DateTimeField("Date Created", auto_now_add=True)

    class Meta:
        app_label = 'beacon'

    def __unicode__(self):
        return "{0} at {1} and {2} ".format(self.name, self.latitude, self.longitude)