from django.db import models
from ticket import Ticket


class TicketItem(models.Model):
    ticket = models.ForeignKey(Ticket)
    menu_item_id = models.CharField(max_length=128)
    name = models.CharField(max_length=128)
    price = models.FloatField()
    date_created = models.DateTimeField("Date Created", auto_now_add=True)
    date_updated = models.DateTimeField("Date Updated", auto_now=True)

    class Meta:
        app_label = 'beacon'

    def __unicode__(self):
        return self.name