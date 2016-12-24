from beaconWeb.apps.beacon.models import Deal, Favorites, SyndicatedDeal, DealPlace, RawPlace
from beaconWeb.apps.beacon.common.utils.places import distance_between_two_points
from fuzzywuzzy import fuzz
from beaconWeb.common_utils import smart_format, remove_non_ascii
from beaconWeb.apps.beacon.retention.emails import send_error_report_email
from fuzzywuzzy import process
from beaconWeb.apps.beacon.data.common_scraper_utils import boundingBox, cities, get_places_in_radius
import traceback


def auto_reject_new_deal_places():
    in_review = DealPlace.objects.filter(in_review=True, place_type__isnull=False)
    auto_reject = ['fast food', 'diner', 'coffee', 'shop', 'office', 'store', 'butcher', 'deli', 'bodega', 'shop', 'bakery', 'hotel', 'veternarian', 'auto', 'supermarket', 'playground', 'truck', "gas station", 'beach', 'farmers', 'college', 'gallery', 'dealership', 'photography', 'dog run', 'building', 'community center', 'food court', 'place', 'joint', 'noodle', 'creperie', 'room', 'preschool', 'lookout', 'gym', 'center', 'pool', 'park', 'studio', 'sports club', 'campground', 'field', 'trail', 'outdoors', 'harbor', 'marina', 'boat', 'ferry', 'martial arts', 'track', 'pier', 'museum', 'garden', 'spa', 'bank', 'zoo', 'chiropractor', 'surf', 'fishing', 'temple', 'beauty', 'bus line', 'professional', 'station', 'non-profit', 'neighborhood', 'furniture', 'salon', 'tattoo', 'room', 'astrologer', 'hall', 'golf', 'tennis', 'church', 'school', 'hospital', 'breakfast', 'festival', 'city', 'general', 'coworking', 'cemetary', 'university', 'construction', 'landscaping', 'services', 'travel', 'transport', 'court', 'startup', 'boutique', 'garage', 'laundry']
    for place in in_review:
        if any(x in place.place_type.lower() for x in auto_reject):
            place.delete()
    print "Auto reject new places successful"


def auto_approve_new_deal_places_for_all_cities():
    for city in cities:
        auto_approve_new_deal_places_for_city(cities[city]['latitude'], cities[city]['longitude'], cities[city]['radius'])


def auto_approve_new_deal_places_for_city(latitude, longitude, radius):
    places = get_places_in_radius(latitude, longitude, radius, True)
    in_review = places.filter(place_type__isnull=False)
    auto_approve_new_deal_places(in_review)


def auto_approve_new_deal_places(deal_places):
    auto_approve = ['nightclub', 'strip club', 'music venue', 'bar', 'pub', 'restaurant', 'brewery', 'wine', 'comedy', 'lounge', 'speakeasy', 'beer']
    exclude = ['barbershop', 'fast food', 'shop', 'store']
    for place in deal_places:
        if any(x in place.place_type.lower() for x in auto_approve) and not any(x in place.place_type.lower() for x in exclude):
            place.in_review = False
            place.save()
    print "Auto approve new deal places successful"


def get_possible_event_venues(latitude, longitude, radius):
    latitude_min, longitude_min, latitude_max, longitude_max = boundingBox(latitude, longitude, radius)
    places = DealPlace.objects.filter(latitude__range=(latitude_min, latitude_max), longitude__range=(longitude_min, longitude_max))
    bad_names = ['bistro', 'ristorante', 'burger', 'hookah', 'smoke', 'wine', 'restaurant']
    types = ['pub', 'bar', 'lounge', 'beer', 'nightclub', 'music']
    bad_types = ['comedy', 'wine', 'restaurant', 'grill', 'juice', 'store']
    event_venues = []
    for place in places:
        if place.place_type:
            if any(x in place.place_type.lower() for x in types) and not any(x in place.name.lower() for x in bad_names) and not any(x in place.place_type.lower() for x in bad_types):
                event_venues.append(place)
    return event_venues


def auto_approve_event_venues_for_all_cities():
    for city in cities:
        auto_approve_event_venues(cities[city]['latitude'], cities[city]['longitude'], cities[city]['radius'])


def auto_approve_event_venues(latitude, longitude, radius):
    event_venues = get_possible_event_venues(latitude, longitude, radius)
    for event_venue in event_venues:
        event_venue.in_review = False
        event_venue.save()


def match_and_add_places_from_raw_places_all_cities():
    for city in cities:
        match_and_add_places_from_raw_places(cities[city]['latitude'], cities[city]['longitude'], cities[city]['radius'])


def match_and_add_places_from_raw_places(latitude, longitude, radius):
    errors = []
    latitude_min, longitude_min, latitude_max, longitude_max = boundingBox(latitude, longitude, radius)
    raw_places = RawPlace.objects.filter(latitude__range=(latitude_min, latitude_max), longitude__range=(longitude_min, longitude_max))
    deal_places = DealPlace.objects.all()
    for raw_place in raw_places:
        print str(raw_place.id)
        lat_range = [raw_place.latitude - 0.01, raw_place.latitude + 0.01]
        lng_range = [raw_place.longitude - 0.01, raw_place.longitude + 0.01]
        deal_places_near_raw_place = deal_places.filter(latitude__range=lat_range, longitude__range=lng_range)
        matched_places = []
        for place in deal_places_near_raw_place:
            if fuzz.partial_ratio(remove_non_ascii(place.name), remove_non_ascii(raw_place.name)) > 90:
                matched_places.append(place)
        if len(matched_places) == 0:
            add_raw_place_to_deal_place(raw_place)
        elif len(matched_places) > 1:
            errors.append(str(raw_place.id))
    print "Match and Add Places Successful"
    send_error_report_email("Multiple Raw Places", errors)


def add_raw_place_to_deal_place(raw_place):
    deal_place = DealPlace()
    deal_place.in_review = True
    deal_place.place_description = raw_place.place_description
    deal_place.place_type = raw_place.place_description
    deal_place.longitude = raw_place.longitude
    deal_place.latitude = raw_place.latitude
    deal_place.name = raw_place.name
    deal_place.phone = raw_place.phone
    deal_place.street_address = raw_place.street_address
    deal_place.website = raw_place.website
    deal_place.yelp_id = raw_place.yelp_id
    deal_place.foursquare_id = raw_place.foursquare_id
    deal_place.facebook_id = raw_place.facebook_id
    deal_place.neighborhood = raw_place.neighborhood
    deal_place.save()

# def deal_place_duplicate_check(deal_places):
#     for deal_place in deal_places:
#         if deal_place.website and DealPlace.objects.filter(website__icontains=deal_place.website).count() > 1:
#                 print "MULTIPLE VENUES: " + str(deal_place.website) + " " + str(deal_place.name)
#         elif deal_place.phone and DealPlace.objects.filter(phone__icontains=deal_place.phone).count() > 1:
#                 print "MULTIPLE VENUES: " + str(deal_place.phone) + " " + str(deal_place.name)
#         elif deal_place.street_address and DealPlace.objects.filter(street_address__icontains=deal_place.street_address).count() > 1:
#                 print "MULTIPLE VENUES: " + str(deal_place.street_address) + " " + str(deal_place.name)
#         elif DealPlace.objects.filter(latitude=deal_place.latitude, longitude=deal_place.longitude).count() > 1:
#                 print "MULTIPLE VENUES: Latitude -" + str(deal_place.latitude) + " Longitude -" + str(deal_place.longitude) + " " + str(deal_place.name)

#set for 20km radius around Seattle by default
def get_all_places(radius=20, lat=47.6369484, lng=-122.3625873):
    places = DealPlace.objects.all()
    places_in_area = []
    for place in places:
        dist = distance_between_two_points(place.latitude, place.longitude, lat, lng)
        if dist < radius:
            places_in_area.append(place)
    return places_in_area

#returns dictionary of possible duplicates by name, address, website or phone
#excludes places with same name, phone or website but different addresses
def deal_place_duplicate_check(deal_places):
    name_dct = {}
    address_dct = {}
    website_dct = {}
    phone_dct = {}
    lat_lng_dct = {}
    duplicates = {
        "name": {},
        "address": {},
        "website": {},
        "phone": {}
    }
    for place in deal_places:
        if place.name not in name_dct.keys():
            name_dct[place.name] = [place]
            addresses = [place.street_address]
        elif place.name in name_dct.keys():
            if place.street_address not in addresses:
                name_dct[place.name].append(place)
                addresses.append(place.street_address)
        if place.street_address not in address_dct.keys():
            address_dct[place.street_address] = [place]
        elif place.street_address in address_dct.keys():
            address_dct[place.street_address].append(place)
        if place.website not in website_dct.keys():
            website_dct[place.website] = [place]
            addresses = [place.street_address]
        elif place.website in website_dct.keys():
            if place.street_address not in addresses:
                website_dct[place.website].append(place)
                addresses.append(place.street_address)
        if place.phone not in phone_dct.keys():
            phone_dct[place.phone] = [place]
            addresses = [place.street_address]
        elif place.phone in phone_dct.keys():
            if place.street_address not in addresses:
                phone_dct[place.phone].append(place)
                addresses.append(place.street_address)
    for k, v in name_dct.iteritems():
        if len(v) > 1:
            duplicates["name"][k] = v
    for k, v in address_dct.iteritems():
        if len(v) > 1:
            duplicates["address"][k] = v
    for k, v in website_dct.iteritems():
        if len(v) > 1:
            duplicates["website"][k] = v
    for k, v in phone_dct.iteritems():
        if len(v) > 1:
            duplicates["phone"][k] = v
    for key, value in duplicates.iteritems():
        print key
        for k, v in value.iteritems():
            try:
                matching_attribute = unicode(k)
                print "{0}: {1} places".format(matching_attribute, len(v))
            except:
                continue
        print " "
    return duplicates


def delete_duplicate_places(deal_places):
    duplicated = deal_place_duplicate_check(deal_places)
    for same in duplicated:
        for key in duplicated[same]:
            for x in range(1, len(duplicated[same][key])):
                try:
                    print duplicated[same][key][x]
                    duplicated[same][key][x].delete()
                except:
                    traceback.print_exc()
                    continue


def delete_duplicate_places_for_new_city(latitude, longitude, radius):
    places = get_places_in_radius(latitude,longitude, radius, True)
    delete_duplicate_places(places)


#prints key data fields for a list of places to compare whether they are the same place
def dupe_info(places):
    for place in places:
        print str(place.id) + " " + place.name
        deals = Deal.objects.filter(place=place)
        hh = SyndicatedDeal.objects.filter(place=place)
        favs = Favorites.objects.filter(place=place)
        print "Deals: " + str(len(deals)) + " HH: " + str(len(hh)) + " Favs: " + str(len(favs))
        print "  street_address: " + place.street_address
        print "  lat: " + str(place.latitude)
        print "  long: " + str(place.longitude)
        print "  image_url: " + str(place.image_url)
        print "  yelp_id: " + str(place.yelp_id)
        print "  yelp_rating_image_url: " + str(place.yelp_rating_image_url)
        print "  foursquare_id: " + str(place.foursquare_id)
        print "  facebook_id: " + str(place.facebook_id)
        print "  twitter_id: " + str(place.twitter_id)
        #print "  place_description: " + str(place.place_description)
        print "  email: " + str(place.email)
        print "  website: " + str(place.website)
        print "  events_url: " + str(place.events_url)

#transfers references for favorites and syndicated_deal objects from "replace_places_ids" to "actual_place_id"
def swap_dupes(actual_place_id, replace_places_ids):
    actual_place = DealPlace.objects.get(id=actual_place_id)
    replace_places = DealPlace.objects.filter(id__in=replace_places_ids)
    for place in replace_places:
        deals = Deal.objects.filter(place=place)
        for deal in deals:
            deal.place = actual_place
            deal.save()
        happyhours = SyndicatedDeal.objects.filter(place=place)
        for hh in happyhours:
            hh.place = actual_place
            hh.save()
        favs = Favorites.objects.filter(place=place)
        for fav in favs:
            fav.place = actual_place
            fav.save()
        print "{0}: {1} deals, {2} happy hours, {3} favorites swapped to {4}".format(str(place.id), str(len(deals)), str(len(happyhours)), str(len(favs)), str(actual_place_id))
    print "You can delete_places({0})".format(replace_places_ids)

def delete_places(ids):
    places = DealPlace.objects.filter(id__in=ids)
    for place in places:
        place.delete()
    print "Places deleted"