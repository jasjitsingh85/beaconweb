# from instagram.client import InstagramAPI
from django.contrib.auth.models import User
# from beaconWeb.apps.beacon.common.chron import get_random_user
import requests
import json
import gc
from beaconWeb.apps.beacon.models.profile import Profile
from beaconWeb.apps.beacon.models.deal_place import DealPlace
from beaconWeb.apps.beacon.models.place_photos import PlacePhotos
from random import randint
from datetime import datetime, timedelta
import facebook
import time
from beaconWeb.common_utils import smart_format
# import facebook
from beaconWeb.settings import RQ_THREAD
from django_rq import job

access_token = "201775575.8bbd0dd.a81bcb1b5a1d49ed99da871b85ef01e5"
client_secret = "49d308cf53fe458ca4c6cba2fd13ce47"
# api = InstagramAPI(access_token=access_token, client_secret=client_secret)
base_url = "https://api.instagram.com/v1/locations/"

# user = get_random_user()
# facebook_api = GraphAPI(access_token=user.profile.fb_token)


def sort_and_return_images(deal_place):
    sorted_list = []
    photo_list = list(PlacePhotos.objects.filter(place=deal_place))
    photo_list.sort(key=lambda x: x.like_count, reverse=True)
    count = 0
    while len(sorted_list) <= 10:
        # if photo_list[count].tag_count == 0:
        sorted_list.append(photo_list[count].source_image_url)
        count += 1
    return sorted_list


facebook_errors = []


def update_instagram_ids(deal_places):
    filtered_deal_places = deal_places.filter(facebook_id__isnull=False)
    del facebook_errors[:]
    for deal_place in filtered_deal_places:
         instagram_id = get_instagram_id(deal_place)
         deal_place.instagram_id = instagram_id
         deal_place.save()
    return facebook_errors


def get_random_user():
    profiles = Profile.objects.filter(is_underage=False, fb_token__isnull=False)
    random_index = randint(0, len(profiles) - 1)
    return profiles[random_index].user


def get_instagram_id(deal_place):
    place_id = get_facebook_place_id(deal_place)
    location_id = get_location_id(deal_place, place_id)
    return location_id


def get_facebook_place_id(deal_place):
    user = get_random_user()
    facebook_api = facebook.GraphAPI(user.profile.fb_token)
    facebook_id = deal_place.facebook_id
    try:
        page = facebook_api.get_object(id=facebook_id)
        return page['id']
    except:
        error = "Place ID Failure: " + str(facebook_id) + " " + str(deal_place.id) + " " + deal_place.name
        print error
        facebook_errors.append(error)
        return None


def get_location_id(deal_place, facebook_place_id):
    if facebook_place_id is not None:
        query_string = "search?facebook_places_id={0}&access_token={1}".format(facebook_place_id, access_token)
        url = base_url + query_string
        try:
            response = requests.get(url)
            response = json.loads(response.text)
            if len(response['data']) > 0:
                return response['data'][0]['id']
            else:
                error = "CHECK: " + str(deal_place.facebook_id) + " " + str(deal_place.id) + " " + smart_format(deal_place.name)
                print error
                facebook_errors.append(error)
                return None
        except:
            error = "Location ID Failure: " + str(url)
            print error
            facebook_errors.append(error)
            return None
    else:
        return None


def get_location_media_data(instagram_id):
    query_string = "{0}/media/recent?access_token={1}".format(instagram_id, access_token)
    url = base_url + query_string
    media_list = []
    count = 0
    while url and count < 20:
        media = get_media_in_json(url)
        media_list.extend(media['data'])
        count += 1
        if 'next_url' in media['pagination']:
            url = media['pagination']['next_url']
        else:
            url = None
        time.sleep(1)
    return media_list


def get_media_in_json(url):
    try:
        print url
        response = requests.get(url)
        response = json.loads(response.text)
        return response
    except:
        print "Failure"
        return {"data": [], "pagination": {}}


def cache_instagram_links(deal_place):
    media = get_location_media_data(deal_place.instagram_id)
    media_to_delete = PlacePhotos.objects.filter(place=deal_place)
    media_to_delete.delete()
    for item in media:
        if item['type'] == "image":
            place_photos = PlacePhotos()
            place_photos.place = deal_place
            place_photos.source_image_url = item['images']['standard_resolution']['url']
            place_photos.like_count = item['likes']['count']
            place_photos.comment_count = item['comments']['count']
            place_photos.tag_count = len(item['users_in_photo'])
            place_photos.image_date = datetime.fromtimestamp(int(item['created_time']))
            place_photos.save()
    del media
    gc.collect()


@job(RQ_THREAD)
def get_media_and_cache():
    latitude = 47.6369484
    longitude = -122.3625873
    lat_range = [latitude-0.3, latitude+0.3]
    lng_range = [longitude-0.3, longitude+0.3]
    deal_places = DealPlace.objects.filter(instagram_id__isnull=False, in_review=False, latitude__range=lat_range, longitude__range=lng_range)
    place_ids_with_photos = PlacePhotos.objects.all().values_list('place', flat=True)
    places_with_photos = deal_places.filter(pk__in=place_ids_with_photos)
    places_without_photos = deal_places.exclude(pk__in=place_ids_with_photos)
    for deal_place in places_without_photos:
        cache_instagram_links(deal_place)
    for deal_place in places_with_photos:
        cache_instagram_links(deal_place)