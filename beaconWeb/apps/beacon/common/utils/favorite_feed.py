from django.contrib.auth.models import User
from datetime import datetime, timedelta
from beaconWeb.apps.beacon.models.favorites import Favorites
import twitter
from fuzzywuzzy import fuzz, process
from beaconWeb.apps.beacon.analytics.analytics import excluded_users
from time import mktime
from beaconWeb.apps.beacon.common.constants.deal_status import DEAL_STATUS
from beaconWeb.apps.beacon.models.feed_cache import FeedCache
from beaconWeb.apps.beacon.models.contact import Contact
from beaconWeb.apps.beacon.models.deal_status import DealStatus
from beaconWeb.apps.beacon.models.deal_place import DealPlace
from beaconWeb.apps.beacon.models.event_status import EventStatus
from beaconWeb.apps.beacon.models.image import Image
from beaconWeb.apps.beacon.common.utils.image import send_saw_picture_notification
from beaconWeb.apps.beacon.common.constants.social_sources import SOCIAL_SOURCE
from beaconWeb.apps.beacon.retention.emails import send_marketing_email
from beaconWeb.apps.beacon.common.utils.friends import get_friends_for_favorite_feed
from beaconWeb.apps.beacon.common.utils.deals import get_date_string_for_event
import time
from time import mktime

update_interval_in_minutes = 15


def get_feed_since_last_view(user):
    if user.profile.feed_updated:
        recent_feed = get_favorite_feed(user, user.profile.feed_updated)
    else:
        recent_feed = get_favorite_feed(user)
    return recent_feed


def get_favorite_feed(user, min_date=datetime.now() - timedelta(weeks=1)):
    final_favorite_feed = []
    favorites = Favorites.objects.filter(user=user, active=True)
    t0 = time.time()
    friend_ids = get_friends_for_favorite_feed(user)
    friends = User.objects.filter(pk__in=friend_ids)
    friends_who_joined = get_friends_who_joined(user, min_date)
    friend_pictures = get_friends_with_pictures(friends, min_date)
    friends_who_redeem = get_friends_who_redeem(friends, min_date)
    friends_who_are_going_to_events = get_friends_who_are_going_to_events(friends, min_date)
    places_friends_follow = get_places_friends_followed(friends, min_date)
    # invited_hotspots = ""
    t1 = time.time()
    # twitter_feed = get_twitter_feed(favorites, min_date)
    facebook_feed = get_facebook_feed(user, favorites, min_date)
    t2 = time.time()
    favorite_feed = friends_who_joined + friends_who_redeem + facebook_feed + places_friends_follow + friend_pictures + friends_who_are_going_to_events
    favorite_feed.sort(key=lambda x: x['date_created'], reverse=True)
    for feed_item in favorite_feed:
        feed_item['date_created'] = convert_date(feed_item['date_created'])
        final_favorite_feed.append(feed_item)
    print "Friends Feed: " + str(t1 - t0)
    print "Twitter/FB Feed: " + str(t2 - t1)
    return final_favorite_feed


def get_friends_with_pictures(friends, min_date):
    deal_statuses = DealStatus.objects.filter(user__in=friends, public=True, date_created__gte=min_date).select_related('beacon')
    beacon_ids = DealStatus.objects.filter(user__in=friends, public=True, date_created__gte=min_date).values_list('beacon', flat=True)
    images = Image.objects.filter(user__in=friends, beacon_id__in=beacon_ids, date_created__gte=min_date)
    image_items = []
    for deal_status in deal_statuses:
        user_name = deal_status.user.get_full_name()
        place_name = deal_status.deal.place.name
        new_images = images.filter(user=deal_status.user, beacon=deal_status.beacon)
        for image in new_images:
            status_obj = {"source" : "hotspot"}
            status_obj['date_created'] = image.date_created
            status_obj['message'] = "{0} added a picture at {1}".replace("{0}", user_name).replace("{1}", place_name)
            status_obj['name'] = "{0}".replace("{0}", user_name)
            status_obj['thumbnail'] = deal_status.user.profile.avatar_url
            status_obj['image_url'] = "https://s3.amazonaws.com/hotspot-photo/" + str(image.image_key)
            status_obj['url'] = ""
            status_obj['deal_place_id'] = str(deal_status.deal.place.id)
            image_items.append(status_obj)
    return image_items


def get_places_friends_followed(friends, min_date):
    favorites = Favorites.objects.filter(date_updated__gte=min_date, user__in=friends, active=True).exclude(user_id__in=excluded_users)
    places_followed_by_friends = []
    for favorite in favorites:
        status_obj = {"source" : "hotspot"}
        user = favorite.user
        status_obj['date_created'] = favorite.date_updated
        status_obj['message'] = "{0} followed {1}".replace("{0}", user.get_full_name()).replace("{1}", favorite.place.name)
        status_obj['name'] = "{0}".replace("{0}", user.get_full_name())
        status_obj['thumbnail'] = user.profile.avatar_url
        status_obj['image_url'] = ""
        status_obj['url'] = ""
        status_obj['deal_place_id'] = str(favorite.place.name)
        places_followed_by_friends.append(status_obj)
    return places_followed_by_friends


def get_friends_who_joined(user, min_date):
    contact_phone_numbers = Contact.objects.filter(user=user).values_list('normalized_phone', flat=True)
    friends = User.objects.filter(username__in=contact_phone_numbers, date_joined__gte=min_date)
    friends_who_joined = []
    for friend in friends:
        status_obj = {"source" : "hotspot"}
        status_obj['date_created'] = friend.date_joined
        status_obj['message'] = "{0} joined Hotspot".replace("{0}", friend.get_full_name())
        status_obj['name'] = "{0}".replace("{0}", friend.get_full_name())
        status_obj['thumbnail'] = friend.profile.avatar_url
        status_obj['image_url'] = ""
        status_obj['url'] = ""
        status_obj['deal_place_id'] = "-1"
        friends_who_joined.append(status_obj)
    return friends_who_joined


def get_friends_who_redeem(friends, min_date):
    friends_who_set_hotspots = []
    deal_statuses = list(DealStatus.objects.filter(user__in=friends, public=True, date_created__gte=min_date))
    for deal_status in deal_statuses:
        if deal_status.invited_by is None and deal_status.public:
            user_name = deal_status.user.get_full_name()
            venue_name = deal_status.deal.place.name
            status_obj = {"source" : "hotspot"}
            status_obj['date_created'] = deal_status.date_created
            if deal_status.present:
                status_obj['message'] = "{0} is at {1}. Join them for a ${2} {3}".replace("{0}", user_name).replace("{1}", venue_name).replace("{2}", str(format(deal_status.deal.item_price, '.2f'))).replace("{3}", deal_status.deal.item_name.lower())
            else:
                status_obj['message'] = "{0} is going to {1}. Join them for a ${2} {3}".replace("{0}", user_name).replace("{1}", venue_name).replace("{2}", str(format(deal_status.deal.item_price, '.2f'))).replace("{3}", deal_status.deal.item_name.lower())
            status_obj['name'] = "{0}".replace("{0}", deal_status.user.get_full_name())
            status_obj['thumbnail'] = deal_status.user.profile.avatar_url
            status_obj['image_url'] = ""
            status_obj['url'] = ""
            status_obj['deal_place_id'] = "-1"
            friends_who_set_hotspots.append(status_obj)
    return friends_who_set_hotspots


def get_friends_who_are_going_to_events(friends, min_date):
    friends_who_are_going_to_events = []
    event_statuses = list(EventStatus.objects.filter(user__in=friends, public=True, date_created__gte=min_date))
    for event_status in event_statuses:
        if event_status.public:
            user_name = event_status.user.get_full_name()
            venue_name = event_status.event.place.name
            date_string = get_date_string_for_event(event_status.event.start)
            status_obj = {"source" : "hotspot"}
            status_obj['date_created'] = event_status.date_created
            status_obj['message'] = "{0} is going to the {1} event at {2} on {3}".replace("{0}", user_name).replace("{1}", event_status.event.title).replace("{2}", venue_name).replace("{3}", date_string)
            status_obj['name'] = "{0}".replace("{0}", event_status.user.get_full_name())
            status_obj['thumbnail'] = event_status.user.profile.avatar_url
            status_obj['image_url'] = ""
            status_obj['url'] = ""
            status_obj['deal_place_id'] = "-1"
            friends_who_are_going_to_events.append(status_obj)
    return friends_who_are_going_to_events


def get_twitter_feed(favorites, min_date):
    twitter_statuses = []
    t0 = time.time()
    # update_twitter_cache(favorites, min_date)
    t1 = time.time()
    full_feed_qs = FeedCache.objects.filter(source=SOCIAL_SOURCE.TWITTER)
    for favorite in favorites:
        feed = full_feed_qs.filter(place=favorite.place)
        for item in feed:
            status_obj = {'source': 'twitter'}
            status_obj['date_created'] = item.date_created
            status_obj['thumbnail'] = favorite.place.image_url
            status_obj['image_url'] = item.image_url
            status_obj['url'] = "https://twitter.com/" + str(favorite.place.twitter_id) + "/status/" + str(item.content_id)
            status_obj['message'] = truncate_message(item.message, item.image_url)
            status_obj['deal_place_id'] = item.place.id
            status_obj['name'] = item.place.name
            if status_obj['date_created'] > min_date:
                twitter_statuses.append(status_obj)
    t2 = time.time()
    print "Twitter Profile 1: " + str(t1 - t0)
    print "Twitter Profile 2: " + str(t2 - t1)
    return twitter_statuses


def get_facebook_feed(user, favorites, min_date):
    facebook_statuses = []
    t0 = time.time()
    # update_facebook_cache(user, favorites, min_date)
    t1 = time.time()
    full_feed_qs = FeedCache.objects.filter(source=SOCIAL_SOURCE.FACEBOOK)
    for favorite in favorites:
        feed = full_feed_qs.filter(place=favorite.place)
        for item in feed:
            status_obj = {'source': 'facebook'}
            status_obj['date_created'] = item.date_created
            status_obj['thumbnail'] = favorite.place.image_url
            status_obj['image_url'] = item.image_url
            status_obj['url'] = "https://www.facebook.com/" + str(item.content_id)
            status_obj['deep_link_url'] = "fb://profile/" + str(item.content_id)
            status_obj['deal_place_id'] = item.place.id
            status_obj['name'] = item.place.name
            if item.message is None:
                status_obj['message'] = ""
            else:
                status_obj['message'] = truncate_message(item.message, item.image_url)
            if status_obj['date_created'] > min_date:
                facebook_statuses.append(status_obj)
    t2 = time.time()
    print "Facebook Profile 1: " + str(t1 - t0)
    print "Facebook Profile 2: " + str(t2 - t1)
    return facebook_statuses


def truncate_message(message, image_url):
    if image_url:
        if len(message) >= 70:
            return message[:70] + "..."
        else:
            return message
    else:
        if len(message) >= 200:
            return message[:200] + "..."
        else:
            return message


def follow_or_unfollow_favorite(user, request_data):
    if 'deal_place_id' not in request_data:
        return False
    print "DEAL PLACE ID: " + str(request_data['deal_place_id'])
    deal_place_id = int(request_data['deal_place_id'])
    deal_place = DealPlace.objects.get(pk=deal_place_id)
    # check_if_ids_exist(deal_place)
    if Favorites.objects.filter(user=user, place=deal_place).exists():
        favorite = Favorites.objects.filter(user=user, place=deal_place)[0]
        favorite.active = not favorite.active
        favorite.save()
        return favorite.active
    else:
        favorite = Favorites(user=user, place=deal_place)
        favorite.save()
        return favorite.active


def convert_date(date):
    return mktime(date.timetuple())


def add_time_feed_viewed(user, request_data):
    if 'timestamp' not in request_data:
        return False
    timestamp = float(request_data['timestamp'])
    value = datetime.fromtimestamp(timestamp)
    check_to_send_image_notification(user, value)
    user.profile.feed_updated = value
    user.profile.save()


def check_to_send_image_notification(friend_who_saw_picture, new_time_newsfeed_was_checked):
    min_date = datetime.now() - timedelta(weeks=1)
    last_time_newsfeed_was_checked = friend_who_saw_picture.profile.feed_updated
    friend_ids = get_friends_for_favorite_feed(friend_who_saw_picture)
    friends = User.objects.filter(pk__in=friend_ids)
    print "Friends: " + str(friends)
    deal_statuses = DealStatus.objects.filter(user__in=friends, public=True, date_created__gte=min_date).select_related('beacon')
    beacon_ids = DealStatus.objects.filter(user__in=friends, public=True, date_created__gte=min_date).values_list('beacon', flat=True)
    images = Image.objects.filter(user__in=friends, beacon_id__in=beacon_ids, date_created__gte=min_date)
    for deal_status in deal_statuses:
        new_images = images.filter(user=deal_status.user, beacon=deal_status.beacon)
        for image in new_images:
            print "NEW TIME NEWSFEED CHECKED: " + str(time.mktime(new_time_newsfeed_was_checked.timetuple()))
            print "IMAGE DATE: " + str(time.mktime(image.date_created.timetuple()))
            print "LAST TIME NEWSFEED CHECKED: " + str(time.mktime(last_time_newsfeed_was_checked.timetuple()))
            if time.mktime(new_time_newsfeed_was_checked.timetuple()) > time.mktime(image.date_created.timetuple()) > time.mktime(last_time_newsfeed_was_checked.timetuple()):
                print "Notification to be sent"
                send_saw_picture_notification(deal_status, friend_who_saw_picture)


def follow_redemption_location(user, deal_place):
    check_if_ids_exist(deal_place)
    if Favorites.objects.filter(user=user, place=deal_place).exists():
        favorite = Favorites.objects.filter(user=user, place=deal_place)[0]
        favorite.active = True
        favorite.save()
    else:
        favorite = Favorites(user=user, place=deal_place)
        favorite.save()


def check_if_ids_exist(deal_place):
    # if not deal_place.twitter_id and not deal_place.facebook_id:
    #     html = "missing facebook and twitter: " + deal_place.name
    #     if deal_place.website:
    #         html = html + ", " + deal_place.website
    #     send_marketing_email('william.xu@gethotspotapp.com', 'Will Xu', ['wxu121@gmail.com', 'jazjit.singh@gmail.com'], 'missing an id', '', html, 'missing_id')
    # elif not deal_place.twitter_id:
    #     html = "missing twitter: " + deal_place.name
    #     if deal_place.website:
    #         html = html + ", " + deal_place.website
    #     send_marketing_email('william.xu@gethotspotapp.com', 'Will Xu', ['wxu121@gmail.com', 'jazjit.singh@gmail.com'], 'missing an id', '', html, 'missing_id')
    if not deal_place.facebook_id:
        html = "missing facebook: " + deal_place.name
        if deal_place.website:
            html = html + ", " + deal_place.website
        send_marketing_email('william.xu@gethotspotapp.com', 'Will Xu', ['wxu121@gmail.com', 'jazjit.singh@gmail.com'], 'missing an id', '', html, 'missing_id')

# def add_follow_place_for_old_users():
#     deals = Deal.objects.filter(in_app_payment=True)
#     deal_statuses = DealStatus.objects.filter(deal__in=deals, deal_status=DEAL_STATUS.REDEEMED)
#     for ds in deal_statuses:
#         user = ds.user
#         place = ds.deal.place
#         if user is not None:
#             follow_redemption_location(user, place)

