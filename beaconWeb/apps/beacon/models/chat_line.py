from django.db import models


class ChatLine(models.Model):
    phone = models.CharField(max_length=20)
    date_created = models.DateTimeField("Date Created", auto_now_add=True)

    class Meta:
        app_label = 'beacon'
