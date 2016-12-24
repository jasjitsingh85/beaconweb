from django.contrib import admin
from beaconWeb.apps.beacon.models.content_option import ContentOption
from beaconWeb.apps.beacon.models.beacon import Beacon
from beaconWeb.apps.beacon.models.beacon_follow import BeaconFollow
from beaconWeb.apps.beacon.models.location import Location
from beaconWeb.apps.beacon.models.deal import Deal
from beaconWeb.apps.beacon.models.deal_hours import DealHours
from beaconWeb.apps.beacon.models.deal_place import DealPlace
from beaconWeb.apps.beacon.models.syndicated_deal import SyndicatedDeal
from beaconWeb.apps.beacon.models.market import Market
from beaconWeb.apps.beacon.models.event_manager import EventManager
from beaconWeb.apps.beacon.models.event_staffer import EventStaffer
from beaconWeb.apps.beacon.models.brand_ambassador import BrandAmbassador


# admin.site.register(Deal)
# admin.site.register(DealHours)
# # admin.site.register(DealPlace)
#
# class HappyHourAdmin(admin.ModelAdmin):
#     raw_id_fields = ('place',)
#     list_display = ('place', 'description', 'date_updated', )
#     search_fields = ['place__name']
#     list_filter = ('date_updated', )
#
#
# class HappyHourPlaceAdmin(admin.ModelAdmin):
#     # raw_id_fields = ('place',)
#     # list_display = ('place', 'description', 'date_updated', )
#     search_fields = ['name']
#     list_filter = ('date_updated', )
#
# # admin.site.register(SyndicatedDeal)
#
# admin.site.register(SyndicatedDeal, HappyHourAdmin)
# admin.site.register(DealPlace, HappyHourPlaceAdmin)

admin.site.register(Market)
admin.site.register(EventManager)
admin.site.register(EventStaffer)
admin.site.register(BrandAmbassador)
