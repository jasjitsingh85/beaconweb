import facebook
from beaconWeb.apps.beacon.classes.foursquare_client import FoursquareClient
from beaconWeb.apps.beacon.models.deal_place import DealPlace


def primary_category(names):
    bars = []
    cats = ['club', 'speakeasy', 'lounge', 'karaoke', 'pool', 'irish pub', 'gastropub', 'pub' 'brew', 'event', 'music']
    for each in names:
        for cat in cats:
            if cat in each.lower():
                return each
    for each in names:
        if 'bar' in each.lower():
            bars.append(each)
    if bars:
        return max(bars, key=len)
    if names:
        return names[0]
    else:
        return None

def get_place_type(token, places=DealPlace.objects.filter(latitude__range=(47.5, 47.73), longitude__range=(-122.43, -122.24))):
    graph = facebook.GraphAPI(token)
    for place in places:
        if not place.place_type:
            if place.foursquare_id:
                try:
                    venue = FoursquareClient.shared_client.venues(place.foursquare_id)
                except:
                    print "failed on: ", place.name, place.id
                    continue
                names = []
                for each in venue['venue']['categories']:
                    names.append(each['name'])
                place_type = primary_category(names)
                print place_type
                place.place_type = place_type
                place.save()
            elif place.facebook_id:
                try:
                    venue = graph.get_object(id=place.facebook_id)
                except:
                    print "facebook failed on: ", place.name, place.id
                    continue
                names = []
                if 'category_list' in venue:
                    for each in venue['category_list']:
                        names.append(each['name'])
                    place_type = primary_category(names)
                    print place_type
                    place.place_type = place_type
                    place.save()
            else:
                if place.yelp_id:
                    venue = get_business(place.yelp_id)
                    names = []
                    for each in venue['categories']:
                        names.append(each[0])
                    place_type = primary_category(names)
                    print place_type
                    place.place_type = place_type
                    place.save()