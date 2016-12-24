import math
from fuzzywuzzy import fuzz
from fuzzywuzzy import process
from beaconWeb.apps.beacon.models.deal_place import DealPlace


cities = {'seattle': {'latitude': 47.6369484, 'longitude': -122.3625873, 'radius': 20}, 'portland': {'latitude': 45.52, 'longitude': -122.68, 'radius': 20}}

seattle_lat = 47.6369484
seattle_lng = -122.3625873


def match_place(name, address, website, phone):
    lat_range = [seattle_lat-0.3, seattle_lat+0.3]
    lng_range = [seattle_lng-0.3, seattle_lng+0.3]
    deal_places = DealPlace.objects.filter(latitude__range=lat_range, longitude__range=lng_range)
    return True


def get_lat_and_lng_pairs(lat, lng, radius, increments):
    latitudes = []
    longitudes = []
    bounding_box = boundingBox(lat, lng, radius)
    bottom_right = [bounding_box[0], bounding_box[1]]
    top_left = [bounding_box[2], bounding_box[3]]
    lat_increments = (bottom_right[0] - top_left[0])/increments
    lng_increments = (bottom_right[1] - top_left[1])/increments
    for loop_count in range(increments):
        latitudes.append(bottom_right[0] - (loop_count*lat_increments))
        longitudes.append(bottom_right[1] - (loop_count*lng_increments))
    return latitudes, longitudes


def deg2rad(degrees):
    return math.pi*degrees/180.0
# radians to degrees
def rad2deg(radians):
    return 180.0*radians/math.pi

# Semi-axes of WGS-84 geoidal reference
WGS84_a = 6378137.0  # Major semiaxis [m]
WGS84_b = 6356752.3  # Minor semiaxis [m]


def WGS84EarthRadius(lat):
    # http://en.wikipedia.org/wiki/Earth_radius
    An = WGS84_a*WGS84_a * math.cos(lat)
    Bn = WGS84_b*WGS84_b * math.sin(lat)
    Ad = WGS84_a * math.cos(lat)
    Bd = WGS84_b * math.sin(lat)
    return math.sqrt( (An*An + Bn*Bn)/(Ad*Ad + Bd*Bd) )


def boundingBox(latitudeInDegrees, longitudeInDegrees, halfSideInKm):
    lat = deg2rad(latitudeInDegrees)
    lon = deg2rad(longitudeInDegrees)
    halfSide = 1000*halfSideInKm

    # Radius of Earth at given latitude
    radius = WGS84EarthRadius(lat)
    # Radius of the parallel at given latitude
    pradius = radius*math.cos(lat)

    latMin = lat - halfSide/radius
    latMax = lat + halfSide/radius
    lonMin = lon - halfSide/pradius
    lonMax = lon + halfSide/pradius

    return (rad2deg(latMin), rad2deg(lonMin), rad2deg(latMax), rad2deg(lonMax))

def get_places_in_radius(latitude, longitude, radius, in_review):
    latitude_min, longitude_min, latitude_max, longitude_max = boundingBox(latitude, longitude, radius)
    if in_review:
        places = DealPlace.objects.filter(latitude__range=(latitude_min, latitude_max), longitude__range=(longitude_min, longitude_max), closed=False)
    else:
        places = DealPlace.objects.filter(latitude__range=(latitude_min, latitude_max), longitude__range=(longitude_min, longitude_max), closed=False, in_review=False)
    return places


