from beaconWeb.apps.happy_hours.models import Place, City
from math import radians, cos, sin, asin, sqrt

def get_title(number_of_happy_hours, neighborhood, city, day, time):
    if neighborhood is not None:
        location = "{0}, {1}".format(neighborhood, city)
    else:
        location = city
    title = "Happy Hours in {0} on {1} {2}".format(location, day, time)
    return title


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


# def get_city_from_ip(ip_address):
#     # try:
#     ip_address = "72.213.21.54"
#     location = IpRange.objects.by_ip(ip_address)
#     lat = location.city.latitude
#     lng = location.city.longitude
#     city = get_closest_city(lat, lng)
#     if city is not None:
#         return city
#     else:
#         city = City.objects.get(pk=68)
#         return city
#     # except:
#     #     city = City.objects.get(pk=68)
#     #     return city
#
#
# def get_closest_city(lat, lng):
#     places = Place.objects.distinct('city')
#     city = None
#     for place in places:
#         place_lat = place.latitude
#         place_lng = place.longitude
#         dist = distance(lng, lat, place_lng, place_lat)
#         print dist
#         if dist < 30:
#             city = place.city
#     return city
#
# def distance(lon1, lat1, lon2, lat2):
#     """
#     Calculate the great circle distance between two points
#     on the earth (specified in decimal degrees)
#     """
#     # convert decimal degrees to radians
#     lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
#     # haversine formula
#     dlon = lon2 - lon1
#     dlat = lat2 - lat1
#     a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
#     c = 2 * asin(sqrt(a))
#     km = 6367 * c
#     return km


