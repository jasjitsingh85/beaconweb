from django.db import models


class Employee(models.Model):
    first_name = models.CharField(max_length=128, null=True, blank=True)
    last_name = models.CharField(max_length=128, null=True, blank=True)
    employee_id = models.CharField(max_length=128, null=True, blank=True, unique=True)

    class Meta:
        app_label = 'beacon'

    def __unicode__(self):
        return self.first_name

