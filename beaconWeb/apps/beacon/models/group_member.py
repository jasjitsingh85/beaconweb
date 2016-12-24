from django.db import models
from beaconWeb.apps.beacon.models import Contact
from beaconWeb.apps.beacon.models import ContactGroup


class GroupMember(models.Model):
    group = models.ForeignKey(ContactGroup, related_name="members")
    contact = models.ForeignKey(Contact)
    date_created = models.DateTimeField("Date Created", auto_now_add=True)

    class Meta:
        app_label = 'beacon'