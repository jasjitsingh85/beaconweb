from django.db import models
from deal_place import DealPlace
from django.contrib.auth.models import User


class Favorites(models.Model):
    place = models.ForeignKey(DealPlace, related_name='favorite_place')
    user = models.ForeignKey(User)
    active = models.BooleanField(default=True)
    date_created = models.DateTimeField("Date Created", auto_now_add=True)
    date_updated = models.DateTimeField("Date Updated", auto_now=True)

    class Meta:
        app_label = 'beacon'