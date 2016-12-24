from pygeocoder import Geocoder
from time import sleep
from models import Place, City, Neighborhood


def reverse_geocode_place(place):
    result, success = try_reverse_geocode_until_success(place.latitude, place.longitude)
    if not success:
        return
    print result.state
    print result.neighborhood
    city = place.city
    neighborhood_name = result.neighborhood
    if neighborhood_name:
        neighborhood, created = Neighborhood.objects.get_or_create(city=city, name=neighborhood_name)
        place.neighborhood = neighborhood
        place.save()
    city.state_name = result.state
    city.save()

def geocode_all_places():
    places = Place.objects.filter(neighborhood=None)
    count = places.count()
    idx = 0
    for place in places:
        print "{0} {1}%".format(idx, 100*float(idx)/count)
        reverse_geocode_place(place)
        idx += 1

def try_reverse_geocode_until_success(latitude, longitude):
    success = False
    attempts = 2
    results = []
    geocoder = Geocoder()
    while not success and attempts < 3:
        try:
            results = geocoder.reverse_geocode(latitude, longitude)
            success = True
        except:
            attempts += 1
            sleep(2)
    return results, success