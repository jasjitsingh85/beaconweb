from django.db import models
from market import Market


class BrandAmbassador(models.Model):
    name = models.CharField(max_length=100)
    market = models.ForeignKey(Market)
    phone_number = models.CharField(max_length=100)
    email = models.CharField(max_length=100)
    active = models.BooleanField(default=False)
    promo_code = models.CharField(max_length=20)
    date_created = models.DateTimeField("Date Created", auto_now_add=True)

    class Meta:
        app_label = 'beacon'

    def __unicode__(self):
        return self.name + " in " + self.market.name