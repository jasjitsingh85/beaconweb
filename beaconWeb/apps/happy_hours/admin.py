from django.contrib import admin
from beaconWeb.apps.happy_hours.models import HappyHour, Place


# class HappyHourAdmin(admin.ModelAdmin):
#     raw_id_fields = ('place',)
#     list_display = ('place', 'description', 'date_updated', )
#     search_fields = ['place__name']
#     list_filter = ('date_updated', )
#
# class HappyHourPlaceAdmin(admin.ModelAdmin):
#     # raw_id_fields = ('place',)
#     # list_display = ('place', 'description', 'date_updated', )
#     search_fields = ['name']
#     list_filter = ('date_updated', )
#
# admin.site.register(HappyHour, HappyHourAdmin)
# admin.site.register(Place, HappyHourPlaceAdmin)

