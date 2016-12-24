from django.db import models


class TwilioSMS(models.Model):
    twilio_sid = models.CharField(max_length=128, db_index=True)
    body = models.CharField(max_length=640)
    status = models.CharField(max_length=20)
    direction = models.CharField(max_length=20)
    to_number = models.CharField(max_length=20, db_index=True)
    from_number = models.CharField(max_length=20, db_index=True)
    date_created_twilio = models.DateTimeField(null=True, blank=True)
    date_sent_twilio = models.DateTimeField(null=True, blank=True)
    date_created = models.DateTimeField("Date Created", auto_now_add=True)
