from beaconWeb.apps.beacon.models.location import Location
from beaconWeb.apps.beacon.common.utils.hotspot_follow import get_hotspot_list
from beaconWeb.common_utils import distance_between_two_points
from beaconWeb.common_utils import smart_format
from datetime import datetime, timedelta
from beaconWeb.apps.beacon.models.background_location import BackgroundLocation
from beaconWeb.apps.beacon.common.utils.background_notifications import check_to_send_notification

#Helper functions


#Main functions
def set_location(user, lat, long):
    Location.objects.create(user=user, latitude=lat, longitude=long)
    return True


def check_if_here(user, lat, long):
    hotspots = get_hotspot_list(user)
    #not here if in future
    current_hotspots = []
    for hotspot in hotspots:
        if (hotspot.time - datetime.now()).total_seconds() < 60*60*2:
            current_hotspots.append(hotspot)
    at_hotspot = []
    for hotspot in current_hotspots:
        if distance_between_two_points(hotspot.latitude, hotspot.longitude, lat, long) < 0.35:
            print smart_format("{0} is here", user.first_name)
            at_hotspot.append(hotspot)
    return at_hotspot


def save_background_location(user, request_data_dict):
    lat = float(request_data_dict['latitude'])
    long = float(request_data_dict['longitude'])
    background_location = BackgroundLocation(user=user, latitude=lat, longitude=long)
    background_location.save()

    # if not BackgroundLocation.objects.filter(user=user, date_created__gte=datetime.now()-timedelta(minutes=5)).exists():
    # check_to_send_notification(user, background_location)

    return True

