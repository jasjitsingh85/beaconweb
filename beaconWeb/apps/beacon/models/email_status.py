from django.db import models


class EmailStatus(models.Model):
    email = models.CharField(max_length=200)
    category = models.CharField(max_length=200)
    user_agent = models.CharField(max_length=1000, null=True, blank=True)
    event = models.CharField(max_length=100)
    url = models.CharField(max_length=1000, blank=True, null=True)
    date_created = models.DateTimeField("Date Created", auto_now_add=True)

    class Meta:
        app_label = 'beacon'