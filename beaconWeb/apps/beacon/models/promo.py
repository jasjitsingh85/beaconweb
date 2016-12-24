from django.db import models
from django.contrib.auth.models import User


class Promo(models.Model):
    referring_user = models.ForeignKey(User, null=True, blank=True)
    item_number = models.PositiveSmallIntegerField(default=1)
    promo_code = models.CharField(max_length=50, unique=True)
    date_created = models.DateTimeField("Date Created", auto_now_add=True)

    class Meta:
        app_label = 'beacon'