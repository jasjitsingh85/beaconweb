from django.db import models
from employee import Employee
from beaconWeb.apps.beacon.common.constants.integration_type import INTEGRATION_TYPE
from beaconWeb.apps.beacon.common.constants.pos_system_type import POS_SYSTEM_TYPE


class PointOfSale(models.Model):
    location_id = models.CharField(max_length=128)
    default_order_type_id = models.CharField(max_length=128)
    default_revenue_center_id = models.CharField(max_length=128)
    default_table_id = models.CharField(max_length=128)
    default_employee = models.ForeignKey(Employee)
    tender_type_id = models.CharField(max_length=128)
    integration_type = models.CharField(max_length=10, choices=INTEGRATION_TYPE.ENUM)
    system_type = models.CharField(max_length=10, choices=POS_SYSTEM_TYPE.ENUM)
    point_of_sale_id = models.CharField(max_length=128, blank=True, null=True)

    class Meta:
        app_label = 'beacon'
