from django.db import models
from django.contrib.auth.models import User


class Friendship(models.Model):
    user = models.ForeignKey(User)
    friend = models.ForeignKey(User, related_name='friend')
    is_from_contact = models.BooleanField(default=False)
    is_auto_add = models.BooleanField(default=False)
    is_from_facebook = models.BooleanField(default=False)
    is_blocked = models.BooleanField(default=False)

    class Meta:
        app_label = 'beacon'

    def __unicode__(self):
        return "{0}:{1}".format(self.user.get_full_name(), self.friend.get_full_name())