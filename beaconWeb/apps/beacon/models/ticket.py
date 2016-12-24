from django.db import models
from point_of_sale import PointOfSale
from employee import Employee
from payment import Payment
from django.contrib.auth.models import User


class Ticket(models.Model):
    user = models.ForeignKey(User, related_name='tickets')
    point_of_sale = models.ForeignKey(PointOfSale)
    ticket_id = models.CharField(max_length=128)
    employee = models.ForeignKey(Employee)
    order_type_id = models.CharField(max_length=128)
    revenue_center_id = models.CharField(max_length=128)
    table_id = models.CharField(max_length=128)
    subtotal = models.FloatField(default=0.0)
    other_charges = models.FloatField(default=0.0)
    service_charges = models.FloatField(default=0.0)
    tax = models.FloatField(default=0.0)
    discount = models.FloatField(default=0.0)
    convenience_fee = models.FloatField(default=0.0)
    tip = models.FloatField(default=0.0)
    total = models.FloatField(default=0.0)
    payment = models.ForeignKey(Payment, null=True, blank=True, related_name="tickets")
    date_closed = models.DateTimeField(null=True, blank=True)
    date_created = models.DateTimeField("Date Created", auto_now_add=True)
    date_updated = models.DateTimeField("Date Updated", auto_now=True)

    class Meta:
        app_label = 'beacon'
