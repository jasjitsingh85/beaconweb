from django.db import models
from django.contrib.auth.models import User


class ContactGroup(models.Model):
    user = models.ForeignKey(User, related_name="contact_groups")
    name = models.CharField(max_length=256)
    deleted = models.BooleanField(default=False)
    date_created = models.DateTimeField("Date Created", auto_now_add=True)

    class Meta:
        app_label = 'beacon'

