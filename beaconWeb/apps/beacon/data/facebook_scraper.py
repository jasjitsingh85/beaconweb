from beaconWeb.apps.beacon.models.deal_place import DealPlace
from beaconWeb.apps.beacon.models.profile import Profile
from beaconWeb.apps.beacon.data.common_scraper_utils import get_places_in_radius
from random import randint
import facebook
import traceback
import time


def replace_facebook_ids(deal_places):
    for place in deal_places:
        user = get_random_user()
        facebook_api = facebook.GraphAPI(access_token=user.profile.fb_token)
        lat_lng = str(place.latitude) + ',' + str(place.longitude)
        search = facebook_api.request('search', args={'q': place.name.encode('ascii', 'ignore'), 'center': lat_lng, 'type': 'place', 'distance': 1000})
        if len(search['data']) > 0:
            if str(search['data'][0]['id']) != "110843418940484":
                place.facebook_id = search['data'][0]['id']
                place.save()
        else:
            print "Not Found: " + place.name + " " + str(place.id)


def add_facebook_ids(deal_places):
    deal_places_without_facebook_ids = deal_places.exclude(facebook_id__isnull=False)
    for place in deal_places_without_facebook_ids:
        user = get_random_user()
        try:
            facebook_api = facebook.GraphAPI(access_token=user.profile.fb_token)
            lat_lng = str(place.latitude) + ',' + str(place.longitude)
            search = facebook_api.request('search', args={'q': place.name.encode('ascii', 'ignore'), 'center': lat_lng, 'type': 'place', 'distance': 1000})
            if len(search['data']) > 0:
                if str(search['data'][0]['id']) != "110843418940484":
                    place.facebook_id = search['data'][0]['id']
                    place.save()
            else:
                print "Not Found: " + place.name + " " + str(place.id)
        except Exception:
            print "Failed: " + place.name + " " + str(place.id)
            traceback.print_exc()


def add_facebook_ids_for_new_city(latitude, longitude, radius):
    places = get_places_in_radius(latitude, longitude, radius, False)
    add_facebook_ids(places)


def get_facebook_ids(token, places=DealPlace.objects.filter(latitude__range=(47.5, 47.73), longitude__range=(-122.43, -122.24))):
    graph = facebook.GraphAPI(token)
    for DPO in places:
        if not DPO.facebook_id:
            print DPO.name
            search = graph.request('search', args={'q': DPO.name.encode('ascii', 'ignore') + ' seattle', 'type': 'page'})
            for potvenue in search['data']:
                fbvenue = graph.get_object(id=potvenue['id'])
                if 'location' in fbvenue:
                    if 'latitude' in fbvenue['location'] and 'longitude' in fbvenue['location']:
                        if fbvenue['location']['latitude'] < DPO.latitude + 0.01 and fbvenue['location']['latitude'] > DPO.latitude - 0.01 and fbvenue['location']['longitude'] < DPO.longitude + 0.01 and fbvenue['location']['longitude'] > DPO.longitude - 0.01:
                            DPO.facebook_id = potvenue['id']
                            DPO.save()
                            break


def add_facebook_extras_for_new_city(latitude, longitude, radius):
    places = get_places_in_radius(latitude, longitude, radius, False)
    add_facebook_extras(places)


def add_facebook_extras(deal_places):
    deal_places_without_website = deal_places.filter(website__isnull=True, facebook_id__isnull=False)
    failed_ids = []
    for place in deal_places_without_website:
        time.sleep(0.5)
        try:
            user = get_random_user()
            facebook_api = facebook.GraphAPI(access_token=user.profile.fb_token)
            venue = facebook_api.get_object(id=place.facebook_id)
            if not place.website and 'website' in venue:
                print place.name + " " + venue['website']
                place.website = venue['website']
            if not place.place_description and 'about' in venue:
                print place.name + " " + venue['about']
                place.place_description = venue['about']
            print place.name
            place.save()
        except:
            failed_ids.append(place.id)
            "FAILED: " + str(place.id) + " " + place.name
    return failed_ids


def get_random_user():
    profiles = Profile.objects.filter(is_underage=False, fb_token__isnull=False)
    random_index = randint(0, profiles.count() - 1)
    return profiles[random_index].user


def update_facebook_ids_and_names():
    profiles = Profile.objects.filter(fb_token__isnull=False)
    for profile in profiles:
        update_facebook_id_and_name(profile.user)


def update_facebook_id_and_name(user):
    try:
        facebook_api = facebook.GraphAPI(access_token=user.profile.fb_token)
        me = facebook_api.get_object(id='me')
        user.profile.facebook_id = me['id']
        user.profile.save()
        user.first_name = me['first_name']
        user.last_name = me['last_name']
        if 'email' in me:
            user.email = me['email']
        user.save()
    except Exception:
        traceback.print_exc()