from django.db import models
from tab import Tab
from deal import Deal


class TabItem(models.Model):
    tab = models.ForeignKey(Tab)
    menu_item_id = models.CharField(max_length=128)
    overall_item_id = models.CharField(max_length=128)
    name = models.CharField(max_length=128)
    price = models.DecimalField(max_digits=6, decimal_places=2)
    deal = models.ForeignKey(Deal, null=True, blank=True)
    date_created = models.DateTimeField("Date Created", auto_now_add=True)
    date_updated = models.DateTimeField("Date Updated", auto_now=True)

    class Meta:
        app_label = 'beacon'

    def __unicode__(self):
        return self.name