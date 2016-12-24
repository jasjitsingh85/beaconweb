from django.db import models
from django.contrib.auth.models import User


class BackgroundLocation(models.Model):
    user = models.ForeignKey(User, related_name='background_locations')
    longitude = models.FloatField()
    latitude = models.FloatField()
    date_created = models.DateTimeField("Date Created", auto_now_add=True)

    class Meta:
        app_label = 'beacon'

    def __unicode__(self):
        return "{0} at {1} and {2} ".format(self.user.username, self.latitude, self.longitude)
