from beaconWeb.apps.beacon.models.deal_place import DealPlace
from beaconWeb.apps.beacon.classes.foursquare_client import FoursquareClient
from beaconWeb.common_utils import smart_format, remove_non_ascii
from beaconWeb.apps.beacon.data.common_scraper_utils import get_places_in_radius
import time
import traceback


def get_venue_foursquareid(deal_place):
    venue_parameters = {}
    venue_parameters['radius'] = 500
    venue_parameters['ll'] = "{0},{1}".format(deal_place.latitude, deal_place.longitude)
    venue_parameters['query'] = deal_place.name
    try:
        results = FoursquareClient.shared_client.venues.search(venue_parameters)
        if results['venues']:
            print remove_non_ascii(deal_place.name) + results['venues'][0]['name']
            return results['venues'][0]['id']
        else:
            return None
    except:
        print "Foursquare ID Failed: " + deal_place.name


def add_foursquare_ids_for_new_city(latitude, longitude, radius):
    places = get_places_in_radius(latitude, longitude, radius, True)
    add_foursquare_ids(places)


def add_foursquare_ids(deal_places):
    places_without_foursquare_ids = deal_places.filter(foursquare_id__isnull=True)
    for place in places_without_foursquare_ids:
        place.foursquare_id = get_venue_foursquareid(place)
        place.save()


def add_foursquare_extras_for_new_city(latitude, longitude, radius):
    places = get_places_in_radius(latitude, longitude, radius, True)
    add_foursquare_extras(places)


def add_foursquare_extras(deal_places):
    places_with_foursquare_id = deal_places.filter(foursquare_id__isnull=False)
    for place in places_with_foursquare_id:
        if not place.place_description or not place.website or not place.place_type:
            time.sleep(1)
            print remove_non_ascii(place.name)
            try:
                venue = FoursquareClient.shared_client.venues(place.foursquare_id)['venue']
                if not place.place_description and 'description' in venue:
                    print place.name + " " + venue['description']
                    place.place_description = venue['description']

                if not place.website and 'url' in venue:
                    print place.name + " " + venue['url']
                    place.website = venue['url']

                if not place.place_type and 'categories' in venue:
                    if len(venue['categories']) > 0:
                        print place.name + " " + venue['categories'][0]['name']
                        place.place_type = venue['categories'][0]['name']
            except Exception:
                print "Failed"
                traceback.print_exc()
            place.save()