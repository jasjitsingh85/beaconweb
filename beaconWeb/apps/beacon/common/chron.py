from random import randint
from beaconWeb.apps.beacon.data.yelp_scraper import get_yelp_ratings, close_venues_for_all_cities, add_places_from_yelp_for_all_cities
from beaconWeb.apps.beacon.retention.emails import send_error_report_email, send_marketing_email
import pytz
import time
from beaconWeb.apps.beacon.common.utils.friends import update_all_friendships
from beaconWeb.apps.beacon.analytics.analytics import *
from beaconWeb.apps.beacon.common.constants.notification_types import NOTIFICATION_TYPE
from beaconWeb.apps.beacon.common.constants.social_sources import SOCIAL_SOURCE
from beaconWeb.apps.beacon.common.utils.events import add_event, adjust_to_server_timezone, update_event
from beaconWeb.apps.beacon.common.utils.favorite_feed import get_feed_since_last_view
from beaconWeb.apps.beacon.common.utils.tracker import track_notification
from beaconWeb.apps.beacon.data.instagram_scraper import update_instagram_ids
from beaconWeb.apps.beacon.models.feed_cache import FeedCache
from beaconWeb.apps.beacon.models.event_status import EventStatus
from beaconWeb.apps.beacon.models.market import Market
from beaconWeb.apps.beacon.models.cash_payment import CashPayment
from beaconWeb.apps.beacon.models.syndicated_events import SyndicatedEvents
from beaconWeb.apps.beacon.models.emails import Emails
from beaconWeb.apps.beacon.models.view_tracker import ViewTracker
from beaconWeb.apps.beacon.retention.emails import send_winback_email, send_user_interview_request
from beaconWeb.apps.beacon.retention.push import free_drink_retention_push
from beaconWeb.apps.beacon.tasks.send_sms import send_sms
from beaconWeb.apps.push_notifications.utils import update_badge_number
from beaconWeb.apps.beacon.data.facebook_scraper import add_facebook_ids, add_facebook_extras, update_facebook_ids_and_names
from beaconWeb.apps.beacon.data.foursquare_scraper import add_foursquare_ids, add_foursquare_extras
from beaconWeb.apps.beacon.data.place_scraper import match_and_add_places_from_raw_places_all_cities, auto_approve_event_venues_for_all_cities, auto_approve_new_deal_places_for_all_cities
from beaconWeb.apps.beacon.data.happy_hour_scraper import scrape_happy_hours_for_all_cities
from beaconWeb.apps.beacon.data.common_scraper_utils import boundingBox, cities
from beaconWeb.apps.beacon.data.website_scraper import scrape_websites_for_all_cities
from beaconWeb.apps.beacon.common.utils.user_profile import check_if_user_is_underage
from beaconWeb.apps.beacon.analytics.updated_analytics import sea_lat, sea_lng, standard_radius, get_users_with_redemptions
from beaconWeb.apps.beacon.common.utils.point_of_sale import cancel_tab, update_tab_and_tab_item_objects, close_tab
from beaconWeb.apps.beacon.models.tab import Tab
from beaconWeb.apps.beacon.models.sponsored_event import SponsoredEvent
from beaconWeb.apps.beacon.models.sms_conversation import SmsConversation
import traceback
from datetime import datetime, timedelta
import gc
import requests
import json
from beaconWeb.settings import RQ_THREAD
from facebookads.adobjects.customaudience import CustomAudience
from django_rq import job


local_tz = pytz.timezone('America/Chicago')

seattle_latitude = 47.6369484
seattle_longitude = -122.3625873
lat_range = [seattle_latitude-0.3, seattle_latitude+0.3]
lng_range = [seattle_longitude-0.3, seattle_longitude+0.3]

excluded_deals = [207]

# profiles = Profile.objects.filter(is_underage=False, fb_token__isnull=False)
# profile_length = len(profiles)


@job(RQ_THREAD)
def update_newsfeed_cache():
    print "Newsfeed Cache Updating Started"
    min_date = datetime.now() - timedelta(weeks=1)
    places = DealPlace.objects.filter(facebook_id__isnull=False, in_review=False, latitude__range=lat_range, longitude__range=lng_range)
    update_facebook_cache(places, min_date)
    print "Newsfeed Cache Updated"


@job(RQ_THREAD)
def close_chat_lines():
    events = SponsoredEvent.objects.filter(end__lte=datetime.now())
    sms_conversations = SmsConversation.objects.filter(event__in=events)
    for conversation in sms_conversations:
        conversation.active = False
        conversation.save()


@job(RQ_THREAD)
def daily_chron_job():
    # users = get_user_within_distance(47.667759, -122.312766, 20)
    print "Daily Chron Job Started"
    users = User.objects.all()
    update_all_friendships(users)
    min_date = datetime.now() - timedelta(weeks=1)
    # places = DealPlace.objects.filter(facebook_id__isnull=False, in_review=False, latitude__range=lat_range, longitude__range=lng_range)
    # return_unused_rewards()
    # send_follow_up_download_texts()
    # update_underage_status()
    # update_facebook_events(places, min_date)
    update_facebook_ids_and_names()
    # update_ios_badge_alert()
    print "Daily Chron Job Successful"



def weekly_chron_job():
    free_drink_retention_push()
    send_winback_drinks()
    send_user_interview_requests(50)


def first_weekly_data_job():
    add_places_from_yelp_for_all_cities()
    scrape_happy_hours_for_all_cities()
    #TODO add places from foursquare()
    print "First Weekly Data Job Successful"


def second_weekly_data_job():
    match_and_add_places_from_raw_places_all_cities()
    update_keys_for_all_cities()
    add_or_update_extras_for_places_for_all_cities()
    scrape_websites_for_all_cities()
    auto_approve_new_deal_places_for_all_cities()
    #auto_approve_event_venues_for_all_cities()
    #auto_reject_new_deal_places()
    #TODO Auto Integrate happy hours
    close_venues_for_all_cities()
    print "Second Weekly Data Job Successful"


def send_user_interview_requests(number_of_requests):
    seattle_users = get_user_within_distance(sea_lat, sea_lng, standard_radius)
    user_qs = get_users_with_redemptions(seattle_users)
    user_qs = user_qs.exclude(date_joined__gte=datetime.now()-timedelta(weeks=2))
    profiles = Profile.objects.filter(user__in=user_qs).exclude(date_of_interview__isnull=False).exclude(date_contacted_for_interview__isnull=False)
    random_profiles = profiles.order_by('?')[:number_of_requests]
    for profile in random_profiles:
        send_user_interview_request(profile.user)
        profile.date_contacted_for_interview = datetime.now()
        profile.save()


#Helpers
def update_underage_status():
    fb_profiles = Profile.objects.filter(fb_token__isnull=False)
    for profile in fb_profiles:
        profile.is_underage = check_if_user_is_underage(profile.fb_token)
        profile.save()


def update_ios_badge_alert():
    android_user_ids = AndroidDevice.objects.all().values_list('user', flat=True)
    users = get_user_within_distance(47.667759, -122.312766, 20)
    filtered_users = users.exclude(pk__in=android_user_ids)
    for user in filtered_users:
        try:
            feed = get_feed_since_last_view(user)
            count = len(feed)
            if count > 0:
                print "BADGE UPDATED: " + user.get_full_name() + " " + str(count)
                print ""
                update_badge_number(user, count)
        except Exception:
            traceback.print_exc()


def add_places_to_review():
    add_places_from_yelp()
    # add_places_from_foursquare()
    # add_places_from_facebook()
    # approve_non_duplicates_and_send_report_about_potential_duplicates()


def add_or_update_extras_for_places_for_all_cities():
    for city in cities:
        add_or_update_extras_for_places(cities[city]['latitude'], cities[city]['longitude'], cities[city]['radius'])


def add_or_update_extras_for_places(latitude, longitude, radius):
    latitude_min, longitude_min, latitude_max, longitude_max = boundingBox(latitude, longitude, radius)
    deal_places = DealPlace.objects.filter(latitude__range=(latitude_min, latitude_max), longitude__range=(longitude_min, longitude_max))
    add_foursquare_extras(deal_places)
    #TODO add yelp extras
    add_facebook_extras(deal_places)
    get_yelp_ratings(deal_places)
    #TODO add happy hours
    print "Add or update extras successful"


def check_duplicates():
    #TODO
    return True


def update_keys_for_all_cities():
    for city in cities:
        update_keys(cities[city]['latitude'], cities[city]['longitude'], cities[city]['radius'])


def update_keys(latitude, longitude, radius):
    latitude_min, longitude_min, latitude_max, longitude_max = boundingBox(latitude, longitude, radius)
    deal_places = DealPlace.objects.filter(latitude__range=(latitude_min, latitude_max), longitude__range=(longitude_min, longitude_max))
    add_facebook_ids(deal_places)
    add_foursquare_ids(deal_places)
    # add_yelp_ids(deal_places)
    facebook_errors = update_instagram_ids(deal_places)
    print "Update Keys Successful"
    send_error_report_email("Facebook Errors", facebook_errors)


def return_unused_rewards():
    deal_statuses = DealStatus.objects.filter(payment_authorization="REWARD", date_created__lte=datetime.now()-timedelta(days=1)).exclude(deal_status=DEAL_STATUS.REDEEMED)
    for ds in deal_statuses:
        ds.payment_authorization = "UNREDEEMED_REWARD"
        ds.save()
        reward_item = RewardItem(user=ds.user)
        reward_item.save()
    print "Returned Drinks: " + str(len(deal_statuses))
    print ""


# def send_free_drink_reminder():
#     message = "You still have a free drink waiting on Hotspot. Redeem it soon!"
#     android_user_ids = AndroidDevice.objects.all().values_list('user', flat=True)
#     reward_items = RewardItem.objects.filter(isRedeemed=False).values_list('user_id', flat=True)
#     users = get_user_within_distance(47.667759, -122.312766, 20)
#     filtered_users = users.filter(pk__in=reward_items).exclude(pk__in=android_user_ids)
#     for user in filtered_users:
#         send_hotspot_push([user], message)


def send_follow_up_download_texts(lat=47.667759, lng=-122.312766, distance=20):
    users = get_user_within_distance(lat, lng, distance)
    profiles = Profile.objects.filter(user__in=users)
    contact_statuses = ContactStatus.objects.filter(second_sms_sent=False)
    unique_phone_numbers = []
    number_of_website_text_messages_sent = 0
    message = "You still have time to get your first drink for free, worth $5. Download Hotspot to redeem:\nwww.GetHotspotApp.com"
    website_install_info = get_website_install_info(profiles, contact_statuses)
    website_noninstalls = website_install_info['website_noninstalls']
    for contact_status in website_noninstalls:
        if contact_status.phone_number not in unique_phone_numbers:
            unique_phone_numbers.append(contact_status.phone_number)
            send_sms(message, [contact_status.phone_number])
            contact_status.second_sms_sent = True
            contact_status.save()
            number_of_website_text_messages_sent += 1
            print "Number of Website Text Messages Sent: " + str(number_of_website_text_messages_sent)


def send_winback_drinks(lat=47.667759, lng=-122.312766, distance=20, now = datetime.now()):
    users = get_user_within_distance(lat, lng, distance)
    old_users = users.filter(date_joined__lt=now-timedelta(weeks=2))
    venues = get_venues_within_distance(lat, lng, distance)
    deals = Deal.objects.filter(place__in=venues, active=True, in_app_payment=True)
    excluded_beacons = Beacon.objects.filter(creator_id__in=excluded_users)
    hotspot_ids = DealStatus.objects.filter(deal__in=deals).values_list('beacon_id', flat=True).distinct().exclude(beacon__in=excluded_beacons)
    hotspots = Beacon.objects.filter(pk__in=hotspot_ids).exclude(cancelled=True)
    paid_deal_statuses = DealStatus.objects.filter(beacon__in=hotspots)
    paid_redemptions = paid_deal_statuses.filter(deal_status=DEAL_STATUS.REDEEMED).exclude(payment_authorization="REWARD")
    reward_redemptions = paid_deal_statuses.filter(payment_authorization="REWARD", deal_status=DEAL_STATUS.REDEEMED)
    count = 0
    for user in old_users:
        if not RewardItem.objects.filter(user=user).exists():
            if not paid_redemptions.filter(user=user).exists() and not reward_redemptions.filter(user=user).exists():
                reward_item = RewardItem(user=user)
                reward_item.date_expired = datetime.now() + timedelta(days=31)
                reward_item.save()
                send_winback_email(user)
                track_notification(user, NOTIFICATION_TYPE.WINBACK_EMAIL)
                print "Winback drink sent to: " + user.email


# def send_hh_email():
#     views = ViewTracker.objects.filter(view_type='HH')
#     hh_ids = []
#     for view in views:
#         hh_ids.append(view.view_id)
#     hh_ids = list(set(hh_ids))
#     html = "<a>"
#     for hh_id in hh_ids:
#         try:
#             hh = SyndicatedDeal.objects.get(id=hh_id)
#         except:
#             print "No happy hour found for: " + str(hh_id)
#             continue
#         if hh.date_updated < datetime.now() - timedelta(weeks=12):
#             if hh.place.latitude < 47.81 and hh.place.latitude > 47.41 and hh.place.longitude < -122.13 and hh.place.longitude > -122.53:
#                 html = html + "Name: " + hh.place.name + " ID: " + str(hh_id) + "<br>"
#     html = html + "</a>"
#     send_marketing_email('william.xu@gethotspotapp.com', 'Will Xu', ['wxu121@gmail.com'], 'missing a happy hour', '', html, 'missing_id')
#     print "Email sent"


# def update_twitter_cache(places, min_date):
#     twitter_api = twitter.Api(consumer_key=settings.TWITTER_CONSUMER_KEY, consumer_secret=settings.TWITTER_CONSUMER_SECRET, access_token_key=settings.TWITTER_ACCESS_TOKEN, access_token_secret=settings.TWITTER_ACCESS_TOKEN_SECRET)
#     twitter_items_qs = FeedCache.objects.filter(source=SOCIAL_SOURCE.TWITTER)
#     for place in places:
#         twitter_id = place.twitter_id
#         # if twitter_id is not None:
#         twitter_items = twitter_items_qs.filter(place=place)
#         #     current_time = datetime.now()
#         #     if twitter_items.count() > 0:
#         #         last_updated = twitter_items[0].date_updated
#         #     else:
#         #         last_updated = min_date
#         #     # print "CURRENT TIME TWITTER: " + str(current_time)
#         #     # print "LAST UPDATED TWITTER: " + str(last_updated)
#         #     if current_time-timedelta(minutes=15) > last_updated:
#         twitter_items.delete()
#         try:
#             feed_statuses = []
#             statuses = twitter_api.GetUserTimeline(screen_name=twitter_id, include_rts=False, exclude_replies=True)
#             for status in statuses:
#                 timestamp = status.created_at
#                 date_before_offset = datetime.strptime(timestamp, '%a %b %d %H:%M:%S +0000 %Y')
#                 date_created = utc_to_local(date_before_offset)
#                 message = status.text
#                 content_id = status.id
#                 image_url = None
#                 if status.media:
#                     if status.media[0]['type'] == 'photo':
#                         image_url = status.media[0]['media_url_https']
#
#                 feed_cache = FeedCache(place=place, source=SOCIAL_SOURCE.TWITTER, date_created=date_created, message=message, content_id=content_id, image_url=image_url)
#                 feed_statuses.append(feed_cache)
#             FeedCache.objects.bulk_create(feed_statuses)
#         except Exception:
#             print "FEED FAILED TWITTER: " + str(place.id) + " " + place.name + " " + str(place.twitter_id)


def get_random_user():
    profiles = Profile.objects.filter(is_underage=False, fb_token__isnull=False)
    random_index = randint(0, len(profiles) - 1)
    return profiles[random_index].user


def update_facebook_cache(places, min_date):
    facebook_items_qs = FeedCache.objects.filter(source=SOCIAL_SOURCE.FACEBOOK)
    places = places.exclude(facebook_id=None)
    for place in places:
        user = get_random_user()
        facebook_api = facebook.GraphAPI(access_token=user.profile.fb_token)
        facebook_id = place.facebook_id
        facebook_items = facebook_items_qs.filter(place=place)
        facebook_items.delete()
        try:
            print "PLACE NAME: " + str(place.name)
            feed_statuses = []
            statuses = facebook_api.get_object(id=facebook_id + "/posts")
            for status in statuses['data']:
                timestamp = status['created_time']
                date_before_offset = datetime.strptime(timestamp, '%Y-%m-%dT%H:%M:%S+0000')
                date_created = utc_to_local(date_before_offset)
                min_date_with_offset = utc_to_local(min_date)
                content_id = status['id']
                image_url = None
                message = None
                if date_created > min_date_with_offset:
                    posttype = status['type']
                    if posttype == 'photo':
                        image_url = facebook_api.get_object(id=status['object_id'])['source']
                        if 'message' in status:
                            if status['message']:
                                message = status['message']
                    elif posttype == 'status':
                        message = status['message']
                    elif posttype == 'event':
                        # name = status['name']
                        message = status['description']
                        # status_obj['link'] = status['link']
                    elif posttype == 'link':
                        if 'message' in status:
                            message = status['message']
                            # status_obj['link'] = status['link']
                    feed_cache = FeedCache(place=place, source=SOCIAL_SOURCE.FACEBOOK, date_created=date_created, message=message, content_id=content_id, image_url=image_url)
                    feed_statuses.append(feed_cache)
            FeedCache.objects.bulk_create(feed_statuses)
        except Exception:
            print "FEED FAILED FACEBOOK: " + str(place.id) + " " + place.name + " " + str(place.facebook_id)
            traceback.print_exc()
    print "Newsfeed update complete"


def update_facebook_events(places, min_date):
    places = places.exclude(facebook_id=None)
    for place in places:
        user = get_random_user()
        facebook_api = facebook.GraphAPI(access_token=user.profile.fb_token)
        facebook_id = place.facebook_id
        try:
            events = facebook_api.get_object(id=facebook_id + "/events")
            add_facebook_events_to_syndicated_deals(place, events)
        except Exception:
            print "FEED FAILED FACEBOOK: " + str(place.id) + " " + place.name + " " + str(place.facebook_id)
            traceback.print_exc()
    print "Event update complete"

def utc_to_local(utc_dt):
    local_dt = utc_dt.replace(tzinfo=pytz.utc).astimezone(local_tz)
    return local_tz.normalize(local_dt)


def add_facebook_events_to_syndicated_deals(place, events):
    paging = True
    add_events(place, events['data'])
    while paging:
        if 'paging' in events:
            if 'next' in events['paging']:
                url = events['paging']['next']
                response = requests.get(url)
                events = json.loads(response.text)
                add_events(place, events['data'])
            else:
                paging = False
        else:
            paging = False


def add_events(place, events):
    #speed optimization..
    event_ids = []
    for event in events:
        event_id = str(event['id'])
        event_ids.append(event_id)
    events_in_db = SyndicatedEvents.objects.filter(event_id__in=event_ids)

    for event in events:
        title = event['name'].encode('ascii', 'ignore')
        date = event['start_time']
        truncated_date = date.split(':')[0] + ":" + date.split(':')[1]
        stripped_date = datetime.strptime(truncated_date,"%Y-%m-%dT%H:%M")
        event_id = str(event['id'])
        if events_in_db.filter(event_id=event_id).exists():
            update_event(place, title, adjust_to_server_timezone(stripped_date), event_id)
        else:
            add_event(place, title, adjust_to_server_timezone(stripped_date), event_id)


def check_for_unclaimed_tabs_to_cancel():
    try:
        two_hours_prior = datetime.now() - timedelta(hours=2)
        unclaimed_tabs = Tab.objects.filter(tab_claimed=False, closed=False, cancelled=False, date_created__lt=two_hours_prior)
        for unclaimed_tab in unclaimed_tabs:
            updated_tab, tab_items = update_tab_and_tab_item_objects(unclaimed_tab)
            if not updated_tab.tab_claimed and len(tab_items) < 1:
                cancel_tab(updated_tab)
        print "finished checking for unclaimed tabs to cancel"
    except:
        print "FAIL: check_for_unclaimed_tabs_to_cancel"
        send_marketing_email("info@gethotspotapp.com", "CHRON ERROR", ['wxu121@gmail.com'], "CHRON ERROR in check_for_unclaimed_tabs_to_cancel", "CHRON ERROR in check_for_unclaimed_tabs_to_cancel", "CHRON ERROR in check_for_unclaimed_tabs_to_cancel", "test")


def check_for_open_tabs_to_close():
    try:
        six_hours_prior = datetime.now() - timedelta(hours=6)
        open_tabs = Tab.objects.filter(tab_claimed=True, closed=False, cancelled=False, date_created__lt=six_hours_prior)
        for tab in open_tabs:
            close_tab(tab)
        print "finished checking for open tabs to close"
    except:
        print "FAIL: check_for_open_tabs_to_close"
        send_marketing_email("info@gethotspotapp.com", "CHRON ERROR", ['wxu121@gmail.com'], "CHRON ERROR in check_for_open_tabs_to_close", "CHRON ERROR in check_for_open_tabs_to_close", "CHRON ERROR in check_for_open_tabs_to_close", "test")

@job(RQ_THREAD)
def update_audience_on_facebook():
    audience = CustomAudience('6052606590691')
    email_users = get_all_emails()
    # phone_users = get_all_phone_numbers()
    email_schema = [CustomAudience.Schema.MultiKeySchema.email]
    # phone_schema = [CustomAudience.Schema.MultiKeySchema.phone]
    audience.add_users(email_schema, email_users, is_raw=True)
    # audience.add_users(phone_schema, phone_users, is_raw=True)


def get_all_emails():
    active_event_ids = EventStatus.objects.filter(status="R").values_list('event', flat=True)
    market_ids = SponsoredEvent.objects.filter(pk__in=active_event_ids).values_list('market', flat=True)
    markets = Market.objects.filter(pk__in=market_ids).exclude(pk=1)
    all_emails = []
    for market in markets:
        events_in_market = SponsoredEvent.objects.filter(market=market)
        lat = market.latitude
        lng = market.longitude
        lat_range = [lat - .3, lat + .3]
        lng_range = [lng - .3, lng + .3]
        users_in_location = Location.objects.filter(latitude__range=lat_range, longitude__range=lng_range).exclude(
            user__in=excluded_users).values_list('user', flat=True)
        user_obj = User.objects.filter(pk__in=users_in_location)
        user_emails = user_obj.values_list('email', flat=True)
        submitted_emails = Emails.objects.filter(market=market).values_list('email', flat=True)
        emails_from_cash = CashPayment.objects.filter(event__in=events_in_market).values_list('email', flat=True)
        market_emails = list(user_emails) + list(submitted_emails) + list(emails_from_cash)
        all_emails.extend(market_emails)
    formatted_emails = []
    for email in all_emails:
        if email:
            formatted_emails.append([str(email)])
    return formatted_emails


def get_all_phone_numbers():
    active_event_ids = EventStatus.objects.filter(status="R").values_list('event', flat=True)
    market_ids = SponsoredEvent.objects.filter(pk__in=active_event_ids).values_list('market', flat=True)
    markets = Market.objects.filter(pk__in=market_ids).exclude(pk=1)
    all_numbers = []
    for market in markets:
        lat = market.latitude
        lng = market.longitude
        lat_range = [lat - .3, lat + .3]
        lng_range = [lng - .3, lng + .3]
        users_in_location = Location.objects.filter(latitude__range=lat_range, longitude__range=lng_range).exclude(
            user__in=excluded_users).values_list('user', flat=True)
        user_obj = User.objects.filter(pk__in=users_in_location)
        user_phone_numbers = user_obj.values_list('username', flat=True)
        all_numbers.extend(user_phone_numbers)
    formatted_numbers = []
    for number in all_numbers:
        if number:
            formatted_numbers.append(["1" + str(number)])
    return formatted_numbers