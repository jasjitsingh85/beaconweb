from django.db import models
from django.contrib.auth.models import User


class BlockedFriend(models.Model):
    user = models.ForeignKey(User)
    friend = models.ForeignKey(User, related_name="Friend")
    is_blocked = models.BooleanField(default=True)
    date_created = models.DateTimeField("Date Updated", auto_now_add=True)

    class Meta:
        app_label = 'beacon'

    def __unicode__(self):
        return "{0}:{1}".format(self.user.username, self.friend.username)