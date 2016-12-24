# from django.db import models
# from beaconWeb.apps.beacon.models.deal_place import DealPlace
# from beaconWeb.common_utils import smart_format
#
#
# class MerchantProfile(models.Model):
#     deal_place = models.ForeignKey(DealPlace)
#     email = models.EmailField()
#     password = models.CharField(max_length=50)
#     first_name = models.CharField(max_length=50)
#     last_name = models.CharField(max_length=50, blank=True, null=True)
#     activated = models.BooleanField(default=False)
#     date_created = models.DateTimeField("Date Created", auto_now_add=True)
#
#     class Meta:
#         app_label = 'merchant'
#
#     def __unicode__(self):
#         return smart_format("{0} at {1}", self.first_name, self.deal_place.name)
