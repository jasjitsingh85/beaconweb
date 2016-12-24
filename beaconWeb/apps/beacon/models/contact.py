from django.db import models
from django.contrib.auth.models import User


class Contact(models.Model):
    user = models.ForeignKey(User, related_name='contacts')
    name = models.CharField(max_length=50)
    phone_number = models.CharField(max_length=20)
    normalized_phone = models.CharField(max_length=20, db_index=True)
    date_created = models.DateTimeField("Date Updated", auto_now_add=True)

    class Meta:
        app_label = 'beacon'

    def __unicode__(self):
        return "{0}:{1}".format(self.user.username, self.normalized_phone)

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.normalized_phone == other.normalized_phone
