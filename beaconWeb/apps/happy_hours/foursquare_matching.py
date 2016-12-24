from models import Place
from beaconWeb.apps.beacon.classes.foursquare_client import FoursquareClient
from yelpapi import YelpAPI
import nltk
from beaconWeb.common_utils import smart_format
import traceback
import sys

foursquare_api = FoursquareClient.shared_client


def foursquare_match_place(place):
    ll = "{0},{1}".format(place.latitude, place.longitude)
    query = place.name
    parameters = {"ll": ll, "query": query}
    response = foursquare_api.venues.search(parameters)
    found = None
    idx = 0
    venues = response['venues']
    while not found and idx < len(venues):
        venue = venues[idx]
        name = venue['name']
        name_0 = place.name.lower().replace("'", "")
        name_1 = name.lower().replace("'", "")
        distance = nltk.edit_distance(name_0, name_1)
        distance_normalized = float(distance)/max(len(name_0), len(name_1))
        contains_substring = name_0 in name_1 or name_1 in name_0
        match = distance_normalized < 0.5 or contains_substring
        print smart_format("{0}->{1}, distance:{2} substring:{3} MATCH: {4}",place.name, name, distance, contains_substring, match)
        if match:
            found = venue
        idx += 1
    if found:
        place.foursquare_id = venue['id']
        if 'location' in venue:
            location_data = venue['location']
            if 'address' in location_data:
                place.street_address = venue['location']['address']
        if 'contact' in venue and 'formattedPhone' in venue['contact']:
            place.phone = venue['contact']['formattedPhone']
        place.save()
    else:
        #debugging for now so I don't have to make another query for places ive already searched for
        place.foursquare_id = 'NOT FOUND'
        place.save()


def match_all_places():
    for place in Place.objects.filter(foursquare_id=None):
        try:
            foursquare_match_place(place)
        except Exception, err:
            print traceback.format_exc()
            print sys.exc_info()[0]
