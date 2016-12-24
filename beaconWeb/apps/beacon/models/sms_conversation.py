from django.db import models
from chat_line import ChatLine
from sponsored_event import SponsoredEvent
from django.contrib.auth.models import User


class SmsConversation(models.Model):
    user_one = models.ForeignKey(User, related_name="user_one")
    user_two = models.ForeignKey(User, related_name="user_two")
    event = models.ForeignKey(SponsoredEvent)
    chat_line = models.ForeignKey(ChatLine)
    active = models.BooleanField(default=True)
    date_created = models.DateTimeField("Date Created", auto_now_add=True)

    class Meta:
        app_label = 'beacon'