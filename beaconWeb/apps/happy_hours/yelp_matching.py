from models import Place
from beaconWeb.settings import YELP_CONSUMER_KEY, YELP_TOKEN, YELP_CONSUMER_SECRET, YELP_TOKEN_SECRET
from yelpapi import YelpAPI
import nltk
from beaconWeb.common_utils import smart_format

yelp_api = YelpAPI(YELP_CONSUMER_KEY, YELP_CONSUMER_SECRET, YELP_TOKEN, YELP_TOKEN_SECRET)


def yelp_match_place(place):
    ll = "{0},{1}".format(place.latitude, place.longitude)
    term = place.name
    sort = 0
    limit = 2
    response = yelp_api.search_query(term=term, ll=ll, sort=sort, limit=limit)
    found = None
    idx = 0
    businesses = response['businesses']
    while not found and idx < len(businesses):
        business = businesses[idx]
        name = business['name']
        name_0 = place.name.lower().replace("'", "")
        name_1 = name.lower().replace("'", "")
        distance = nltk.edit_distance(name_0, name_1)
        distance_normalized = float(distance)/max(len(name_0), len(name_1))
        contains_substring = name_0 in name_1 or name_1 in name_0
        match = distance_normalized < 0.5 or contains_substring
        print smart_format("{0}->{1}, distance:{2} substring:{3} MATCH: {4}",place.name, name, distance, contains_substring, match)
        if match:
            found = business
        idx += 1
    if found:
        place.yelp_id = business['id']
        place.save()


def match_all_places():
    for place in Place.objects.all():
        yelp_match_place(place)


