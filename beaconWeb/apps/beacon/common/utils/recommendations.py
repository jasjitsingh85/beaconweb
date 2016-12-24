import sys

from beaconWeb.apps.beacon.classes.foursquare_client import FoursquareClient
from beaconWeb.apps.beacon.common.constants.message_type import MESSAGE_TYPE
from beaconWeb.apps.beacon.models.recommendation import Recommendation
from beaconWeb.apps.beacon.tasks.send_sms import send_hotspot_message
from beaconWeb.common_utils import smart_format
from raven.contrib.django.models import client


def get_bars_near_location(lat, lon, radius=10000):
    bar_category_id = '4bf58dd8d48988d116941735'
    parameters = {}
    parameters['radius'] = radius
    parameters['ll'] = "{0},{1}".format(lat, lon)
    parameters['categoryId'] = bar_category_id
    results = FoursquareClient.shared_client.venues.search(parameters)
    return results['venues']


def get_nearby_bar_for_user(user):
    if not user.locations.exists():
        return None
    location = user.locations.latest('date_created')
    results = get_bars_near_location(location.latitude, location.longitude)
    if not len(results):
        return None
    #get venue we haven't already recommended to user
    already_recommended = list(Recommendation.objects.filter(user=user).values_list('foursquare_venue_id', flat=True))
    rec = None
    found = False
    idx = 0
    while not found and (idx < len(results)):
        result = results[idx]
        foursquare_id = result['id']
        if foursquare_id not in already_recommended:
            found = True
            rec = result
        idx += 1
    return rec


def send_recommendation_notification_to_users(users):
    for user in users:
        try:
            send_recommendation_notification(user)
        except:
            print "Unexpected error:", sys.exc_info()[0]
            client.captureException()
        

def send_recommendation_notification(user):
    if not user.ios_devices.exists() and not user.android_devices.exists():
        return

    message = smart_format("Hey {0}! Looking to get friends together tonight? Set a hotspot.", user.first_name)
    foursquare_id = None
    bar = get_nearby_bar_for_user(user)
    if bar:
        name = bar['name']
        foursquare_id = bar['id']
        location_data = bar['location']
        location = None
        if 'crossStreet' in location_data.keys():
            location = location_data['crossStreet']
        elif 'address' in location_data.keys():
            location = location_data['address']
        if location:
            message = smart_format("Hey {0}! Looking to get friends together tonight? Set a hotspot at {1} ({2}). It's heating up!", user.first_name, name, location)
        else:
            message = smart_format("Hey {0}! Looking to get friends together tonight? Set a hotspot at {1}. It's heating up!", user.first_name, name)
    recommendation = Recommendation.objects.create(user=user, foursquare_venue_id=foursquare_id, message_text=message)
    send_hotspot_message([user], push_text=message, message_type=MESSAGE_TYPE.HOTSPOT_RECOMMENDATION, recommendation_id=recommendation.pk)






