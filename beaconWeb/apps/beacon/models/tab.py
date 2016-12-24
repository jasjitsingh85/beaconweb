from django.db import models
from point_of_sale import PointOfSale
from employee import Employee
from payment import Payment
from django.contrib.auth.models import User
from decimal import Decimal


class Tab(models.Model):
    user = models.ForeignKey(User, related_name='tabs')
    point_of_sale = models.ForeignKey(PointOfSale)
    api_tab_id = models.CharField(max_length=128)
    tab_claimed = models.BooleanField(default=False)
    employee = models.ForeignKey(Employee)
    order_type_id = models.CharField(max_length=128)
    revenue_center_id = models.CharField(max_length=128, null=True, blank=True)
    table_id = models.CharField(max_length=128)
    subtotal = models.DecimalField(default=Decimal('0.00'), max_digits=6, decimal_places=2)
    other_charges = models.DecimalField(default=Decimal('0.00'), max_digits=6, decimal_places=2)
    service_charges = models.DecimalField(default=Decimal('0.00'), max_digits=6, decimal_places=2)
    tax = models.DecimalField(default=Decimal('0.00'), max_digits=6, decimal_places=2)
    discount = models.DecimalField(default=Decimal('0.00'), max_digits=6, decimal_places=2)
    convenience_fee = models.DecimalField(default=Decimal('0.00'), max_digits=6, decimal_places=2)
    tip = models.DecimalField(default=Decimal('0.00'), max_digits=6, decimal_places=2)
    total = models.DecimalField(default=Decimal('0.00'), max_digits=6, decimal_places=2)
    amount_paid = models.DecimalField(default=Decimal('0.00'), max_digits=6, decimal_places=2)
    payment_authorization = models.CharField(max_length=20, blank=True, null=True)
    payment = models.ForeignKey(Payment, null=True, blank=True, related_name="tabs")
    closed = models.BooleanField(default=False)
    cancelled = models.BooleanField(default=False)
    date_closed = models.DateTimeField(null=True, blank=True)
    date_created = models.DateTimeField("Date Created", auto_now_add=True)
    date_updated = models.DateTimeField("Date Updated", auto_now=True)

    class Meta:
        app_label = 'beacon'
