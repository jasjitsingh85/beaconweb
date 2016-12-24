import datetime
from django.db.models import Q
from beaconWeb.apps.beacon.classes.foursquare_client import FoursquareClient
import braintree
from beaconWeb.facebook_ads_api import HotspotFacebookAds
from django.contrib.auth.models import User
from beaconWeb.apps.beacon.models import Payment
from beaconWeb.apps.beacon.models import Beacon
from beaconWeb.apps.beacon.models import BeaconFollow
from beaconWeb.apps.beacon.models import RegionState
from beaconWeb.apps.beacon.models import DealStatus
from beaconWeb.apps.beacon.models import DealPlace
from beaconWeb.apps.beacon.models import Deal
from beaconWeb.apps.beacon.models import Location
from beaconWeb.apps.beacon.models import Friendship
from beaconWeb.apps.beacon.models import Contact
from beaconWeb.apps.beacon.models import Profile
from beaconWeb.apps.beacon.models import ContactStatus
from beaconWeb.apps.beacon.models import RewardItem
from beaconWeb.apps.beacon.models import Promo
from beaconWeb.apps.beacon.models import Favorites
from beaconWeb.apps.beacon.models import NotificationTracker
from beaconWeb.apps.beacon.models import ViewTracker
from beaconWeb.apps.beacon.models import SponsoredEvent
from beaconWeb.apps.beacon.models import EventStatus
from beaconWeb.apps.beacon.models import UserFeedback
from beaconWeb.apps.beacon.models import CashPayment
from beaconWeb.apps.beacon.models import DatingProfile
from beaconWeb.apps.beacon.models import DatingMatch
from beaconWeb.apps.beacon.models import EmailResponse
from beaconWeb.apps.beacon.models import EmailCampaignTracker
from beaconWeb.apps.beacon.models import EmailStatus
from beaconWeb.apps.beacon.models import Market
from beaconWeb.apps.beacon.models import Emails
from beaconWeb.apps.beacon.models import EventStaffer
from beaconWeb.apps.beacon.models import EventManager
from beaconWeb.apps.beacon.models import BrandAmbassador
from beaconWeb.apps.beacon.common.utils.encryption import simple_int_hash
from beaconWeb.apps.beacon.common.constants.event_status import EVENT_STATUS
from beaconWeb.apps.beacon.common.utils.friends import get_friends
from beaconWeb.common_utils import smart_format
from django.db.models import Q
from beaconWeb.apps.push_notifications.models import AndroidDevice
from beaconWeb.apps.beacon.common.constants.deal_status import DEAL_STATUS
from django.db.models import Count
from pygeocoder import Geocoder
from beaconWeb.common_utils import distance_between_two_points
import numpy as np
from datetime import datetime, timedelta
from time import sleep
import twitter
import facebook
from fuzzywuzzy import fuzz
from boto.s3.connection import S3Connection
from boto.s3.key import Key
import urllib
from django.conf import settings
# from facebookads.api import FacebookAdsApi
from facebookads import objects
from beaconWeb.apps.beacon.common.utils.swipe_and_match import get_dating_queue
import requests
import json

#Price Change December 8th, 2015

#Setting
small_radius = 1
standard_radius = 10
large_radius = 20

sea_lat = 47.6369484
sea_lng = -122.3625873

excluded_users = [8739, 7293, 7192, 4380, 1454]
excluded_deals = [178, 207, 210, 213]
friends_to_exclude = [542,500,155,18,6859,4432,4254,248,55,183,636,391,177,7213,4509,5490,25,28,17,11,5491,13281,62,260,5202,5378,343,64,872,66,79,5889,7191,7,1586]
redemption_analytics_cutoff_date = datetime(2015,7,1)

market_dict = {
    "SEA": {"lat" : 47.6369484, "lng": -122.3625873},
    "BAL": {"lat" : 39.2848183, "lng": -76.6905261},
    "NHV": {"lat" : 41.2984267, "lng": -72.999136},
    "DEN": {"lat" : 39.7645183, "lng": -104.9955397},
}


def get_user_within_distance(lat, lng, distance=20, max_date = datetime.now(), min_date = datetime(2016, 1, 1)):
    lat_range = [lat-.3, lat+.3]
    lng_range = [lng-.3, lng+.3]
    users_in_location = Location.objects.filter(latitude__range=lat_range, longitude__range=lng_range, date_created__range=[min_date, max_date]).exclude(user__in=excluded_users).values_list('user', flat=True)
    user_obj = User.objects.filter(pk__in=users_in_location).exclude(pk__in=excluded_users)
    return user_obj


def get_user_within_range(lat, lng, range=0.3, max_date = datetime.now(), min_date = datetime(2016, 1, 1)):
    lat_range = [lat-range, lat+range]
    lng_range = [lng-range, lng+range]
    users_in_location = Location.objects.filter(latitude__range=lat_range, longitude__range=lng_range).exclude(user__in=excluded_users).values_list('user', flat=True)
    user_obj = User.objects.filter(pk__in=users_in_location).exclude(pk__in=excluded_users)
    return user_obj


def get_venues_within_distance(lat, lng, radius=standard_radius, active_only=True):
    venues_within_distance = []
    all_venues = DealPlace.objects.all()
    for venue in all_venues:
        distance = distance_between_two_points(lat, lng, venue.latitude, venue.longitude)
        if distance < radius:
            venues_within_distance.append(venue)
    return venues_within_distance

#seattle_users = get_user_within_distance(sea_lat, sea_lng, large_radius)
#active_seattle_venues = get_venues_within_distance(sea_lat, sea_lng, large_radius)
#active_and_inactive_seattle_venues = get_venues_within_distance(sea_lat, sea_lng, large_radius, False)

def get_redemptions(users, min_date=redemption_analytics_cutoff_date, max_date=datetime.now()):
    deal_statuses = DealStatus.objects.filter(user__in=users, date_created__gte=min_date, date_created__lt=max_date).exclude(user__in=excluded_users).exclude(deal__in=excluded_deals)
    redemptions = deal_statuses.filter(deal_status=DEAL_STATUS.REDEEMED)
    return redemptions


def get_users_with_friend_count(users, friend_count):
    users_with_x_friends = []
    for user in users:
        friends = get_friends(user)
        if len(friends[0]) > friend_count:
            users_with_x_friends.append(user)
    return users_with_x_friends


def get_users_with_redemptions(users, max_date=datetime.now(), min_date=redemption_analytics_cutoff_date):
    user_ids = DealStatus.objects.filter(user__in=users, date_created__gte=min_date, date_created__lt=max_date, deal_status=DEAL_STATUS.REDEEMED).exclude(deal_id__in=excluded_deals).values_list('user', flat=True)
    users_with_redemptions = User.objects.filter(pk__in=user_ids)
    return users_with_redemptions


def get_redemptions_without_duplicates(users, min_date=redemption_analytics_cutoff_date, max_date=datetime.now()):
    all_redemptions = get_redemptions(users, min_date, max_date)
    deals = all_redemptions.exclude(deal__in=excluded_deals).values_list('deal', flat=True).distinct()
    time_window = 6
    unique_redemption_ids = []
    for deal in deals:
        #print "\n" + venue.name
        deal_redemptions = all_redemptions.filter(deal__id=deal)
        user_ids = deal_redemptions.values_list('user', flat=True).distinct()
        for id in user_ids:
            user = User.objects.get(id=id)
            #print "\n" + user.first_name + " " + str(id)
            user_redemptions = deal_redemptions.filter(user=user)
            dates = []
            for r in user_redemptions:
                rdate = (r.date_created - timedelta(hours=4)).date()
                #print str(rdate)
                if rdate not in dates:
                    #print str(r.id)
                    dates.append(rdate)
                    unique_redemption_ids.append(r.id)
    unique_redemptions = DealStatus.objects.filter(id__in=unique_redemption_ids)
    return unique_redemptions


def get_active_power_redeemers(users, redemption_threshold=2, day_threshold=30, end_date=datetime.now()):
    power_redeemers = []
    start_date = end_date - timedelta(days=day_threshold)
    redeemers = get_users_with_redemptions(users,end_date,start_date)
    for user in redeemers:
        redemptions = get_redemptions_without_duplicates([user],start_date,end_date,)
        if len(redemptions) >= redemption_threshold:
            power_redeemers.append(user)
    return power_redeemers


def get_weekly_active_users(min_date=datetime.now()-timedelta(weeks=1), max_date=datetime.now(), lat=sea_lat, lng=sea_lng, distance=standard_radius):
    users = get_user_within_distance(lat, lng, distance)
    user_qs = User.objects.filter(pk__in=[x.pk for x in users])
    users_to_exclude = User.objects.filter(date_joined__gte=min_date, date_joined__lt=max_date)
    active_user_ids = Location.objects.filter(date_created__gte=min_date, date_created__lt=max_date, user__in=user_qs).exclude(user__in=users_to_exclude).values_list('user', flat=True).distinct()
    active_users = User.objects.filter(pk__in=active_user_ids)
    return active_users


def user_permissions(users, android_or_ios="both"):
    has_device = ~(Q(ios_devices=None) & Q(android_devices=None))
    has_location = ~(Q(locations=None))
    has_contacts = ~(Q(contacts=None))
    all_users = User.objects.filter(pk__in=[x.pk for x in users], profile__activated=True)
    android_ids = AndroidDevice.objects.all().values_list('user', flat=True)
    if android_or_ios == "both":
        print "All devices"
        activated_users = all_users
    elif android_or_ios == "iOS":
        print "iOS devices only"
        activated_users = all_users.exclude(pk__in=android_ids)
    elif android_or_ios == "android":
        print "Android devices only"
        activated_users = all_users.filter(pk__in=android_ids)
    total_count = activated_users.count()
    print "total activated users: {0}".format(total_count)
    device_count = activated_users.filter(has_device).count()
    print_permission("device", device_count, total_count)

    location_count = activated_users.filter(has_location).count()
    print_permission("location", location_count, total_count)

    contact_count = activated_users.filter(has_contacts).count()
    print_permission("contacts", contact_count, total_count)

    device_and_location_count = activated_users.filter(has_device & has_location).count()
    print_permission("device+location", device_and_location_count, total_count)

    device_and_contact_count = activated_users.filter(has_device & has_contacts).count()
    print_permission("device+contact", device_and_contact_count, total_count)

    location_and_contact_count = activated_users.filter(has_location & has_contacts).count()
    print_permission("location+contact", location_and_contact_count, total_count)

    device_and_location_and_contact_count = activated_users.filter(has_device & has_location & has_contacts).count()
    print_permission("device+location+contact", device_and_location_and_contact_count, total_count)


def print_permission(description, permission_count, total_count):
    percent = 100*permission_count/float(total_count)
    print "{0} -> {1} : {2:.1f}%".format(description, permission_count, percent)


def filter_contact_status_by_referrer(users, max_date, min_date):
    filtered_contact_statuses = []
    phone_numbers = users.values_list('username', flat=True)
    contact_statuses = ContactStatus.objects.filter(date_created__gte=min_date, referred_phone_number__in=phone_numbers, date_created__lte=max_date, referring_user__in=users).exclude(referring_user__in=excluded_users).exclude(phone_number__isnull=False)
    # distinct_contact_statuses = contact_statuses.distinct('referred_phone_number')
    for contact_status in contact_statuses:
        filtered_contact_statuses.append(contact_status)
    return filtered_contact_statuses


def filter_contact_status(max_date, min_date):
    filtered_contact_statuses = []
    contact_statuses = ContactStatus.objects.filter(date_created__gte=min_date, referred_phone_number__isnull=False, date_created__lte=max_date).exclude(referring_user__in=excluded_users).exclude(phone_number__isnull=False)
    distinct_contact_statuses = contact_statuses.distinct('referred_phone_number')
    for contact_status in contact_statuses:
        filtered_contact_statuses.append(contact_status)
    return filtered_contact_statuses, distinct_contact_statuses


def get_contact_status_registration(contact_statuses):
    registered_user = []
    for contact_status in contact_statuses:
        if contact_status.referred_phone_number is not None:
            phone_number = contact_status.referred_phone_number
            contact_date_created = contact_status.date_created
            if User.objects.filter(username=phone_number, date_joined__gte=contact_date_created).exists():
                user = User.objects.get(username=phone_number)
                registered_user.append(user)
    return list(set(registered_user))


def get_weekly_actives_with_android(lat=sea_lat, lng=sea_lng, distance=standard_radius, start_date = datetime.now(), number_of_weeks=10):
    users = get_user_within_distance(lat, lng, distance)
    venues = get_venues_within_distance(lat, lng, distance)
    deals = Deal.objects.filter(place__in=venues, active=True, in_app_payment=True)
    android_user_ids = AndroidDevice.objects.all().values_list('user', flat=True)
    user_qs = User.objects.filter(pk__in=[x.pk for x in users])
    # user_qs = User.objects.filter(pk__in=android_user_ids)
    excluded_beacons = Beacon.objects.filter(creator_id__in=excluded_users)
    hotspot_ids = DealStatus.objects.filter(deal__in=deals).values_list('beacon_id', flat=True).distinct().exclude(beacon__in=excluded_beacons).exclude(deal__in=excluded_deals)
    deal_statuses = DealStatus.objects.filter(beacon_id__in=hotspot_ids)
    for week in range(0, number_of_weeks):
        today = start_date - timedelta(weeks=week)
        last_week = start_date - timedelta(weeks=week + 1)
        two_weeks_ago = start_date - timedelta(weeks=week + 2)
        users = Location.objects.filter(date_created__gte=last_week, date_created__lt=today, user__in=user_qs).values_list('user', flat=True).distinct()
        # last_week_users = Location.objects.filter(date_created__gte=two_weeks_ago, date_created__lt=last_week, user__in=user_qs).values_list('user', flat=True).distinct()
        total_users_to_date = user_qs.filter(date_joined__lt=today)
        total_users_last_week = user_qs.filter(date_joined__lt=last_week)
        new_users_this_week = len(total_users_to_date) - len(total_users_last_week)
        percentage_increase = new_users_this_week/float(len(total_users_last_week))
        hotspots = Beacon.objects.filter(pk__in=hotspot_ids, date_created__lt=today, date_created__gte=last_week).exclude(cancelled=True)
        this_week_invites = BeaconFollow.objects.filter(beacon__in=hotspots).exclude(invited_by=None)
        contact_statuses, distinct_contact_statuses = filter_contact_status(today, last_week)
        # converted_users = get_converted_users(total_users_to_date, today)
        # promo_code_registrations = get_promo_code_registrations(last_week, today)
        viral_registrations = get_contact_status_registration(contact_statuses)
        additional_promo_code_registrations = get_promo_code_registrations(last_week, today, viral_registrations)
        registrations = len(viral_registrations) + len(additional_promo_code_registrations)
        #in_bar_registrations = get_drink_card_reward_items(last_week, today)
        # invitation_per_weekly_active = float(len(this_week_invites))/len(users)
        # invitation_per_hotspot = float(len(this_week_invites))/len(hotspots)
        users_from_growth = User.objects.filter(date_joined__gte=last_week, date_joined__lt=today, pk__in=users)
        # viral_growth = (len(this_week_invites) * conversion_rate)/len(last_week_users)
        viral_growth = (registrations/float(len(total_users_last_week)))
        hotspots_set = get_hotspots_set(last_week, today)
        paid_deal_statuses = DealStatus.objects.filter(beacon__in=hotspots)
        paid_redemptions = len(paid_deal_statuses.filter(deal_status=DEAL_STATUS.REDEEMED).exclude(payment_authorization="REWARD"))
        reward_redemptions = len(paid_deal_statuses.filter(payment_authorization="REWARD", deal_status=DEAL_STATUS.REDEEMED))
        total_redemptions = paid_redemptions + reward_redemptions
        revenue_this_week = 0
        for deal_status in paid_deal_statuses:
            if deal_status.payment:
                if deal_status.payment.is_submitted:
                    revenue_this_week = revenue_this_week + deal_status.deal.item_price
        if len(contact_statuses) > 0:
            conversion_rate = str(len(viral_registrations)/(float(len(distinct_contact_statuses))))
        else:
            conversion_rate = "0"
        percent_open_radius = get_percent_open_radius(lat, lng, today, last_week)
        users_with_redemptions = get_users_with_redemptions(total_users_to_date, today)
        users_with_follows = get_users_with_follows(today)
        if len(users_with_follows):
            average_follows_per_user = len(Favorites.objects.filter(active=True, user_id__in=users_with_follows))/float(len(users_with_follows))
        else:
            average_follows_per_user = 0
        print "Weekly Actives: " + str(len(users))
        print "Weekly Actives Without New Users: " + str(len(users) - new_users_this_week)
        # print "Retained Percentage Increase: " + str((len(users) - len(last_week_users) - len(users_from_growth))/float(len(last_week_users)))
        print "Total User Percentage Increase: " + str(percentage_increase)
        print "Invitations Sent: " + str(len(distinct_contact_statuses))
        # print "Invitations/Weekly Actives: " + str(invitation_per_weekly_active)
        print "Conversion Rate: " + conversion_rate
        print "(Viral) Registration: " + str(registrations)
        # print "In-Venue Registration: " + str(len(in_bar_registrations))
        print "Viral Growth: " + str(viral_growth)
        # print "Invitations/Hotspot: " + str(invitation_per_hotspot)
        print "Paid Redemptions: " + str(paid_redemptions)
        print "Reward Redemptions: " + str(reward_redemptions)
        print "Total Redemptions: " + str(total_redemptions)
        # print "Hotspots Set: " + str(len(hotspots))
        print "Total users: " + str(len(total_users_to_date))
        print "Percent: " + str(float(len(users))/len(total_users_to_date))
        print "Percent without New Users: " + str(float(len(users) - new_users_this_week)/(len(total_users_to_date) - new_users_this_week))
        # print "Hotspots/Users: " + str(len(hotspots)/float(len(users)))
        # print "% Converted Users: " + str(converted_users)
        print "Users with Redemption: " + str(len(users_with_redemptions))
        print "% Users with Redemption: " + str((len(users_with_redemptions)*100)/float(len(total_users_to_date)))
        print "% Opened in Radius: " + str(percent_open_radius)
        print "Revenue: " + str(revenue_this_week)
        print "Projected ARPU: " + str((revenue_this_week * 52)/float(len(total_users_to_date)))
        print "Number of Users w/Follows: " + str(len(users_with_follows))
        print "Number of Users w/Follows as %: " + str(float(len(users_with_follows)*100)/len(total_users_to_date))
        print "Average Follows/User: " + str(average_follows_per_user)
        print "Average Friends/User: "  + str(get_average_number_of_friends_on_hotspot(total_users_to_date))
        print ""


def redeemer_stats_for_ios(start_date = datetime.now(), number_of_weeks=10):
    android_user_ids = AndroidDevice.objects.all().values_list('user', flat=True)
    seattle_users = get_user_within_distance(sea_lat, sea_lng, large_radius)
    user_qs = get_users_with_redemptions(seattle_users)
    user_qs = user_qs.exclude(pk__in=android_user_ids)
    redemption_qs = get_redemptions_without_duplicates(user_qs, redemption_analytics_cutoff_date, start_date)
    #venues = active_and_inactive_seattle_venues
    #deals = Deal.objects.filter(place__in=venues, active=True, in_app_payment=True)
    #users_in_distance = User.objects.filter(pk__in=[x.pk for x in users])
    #user_qs = get_users_with_redemptions(users_in_distance, datetime.now())
    #excluded_beacons = Beacon.objects.filter(creator_id__in=excluded_users)
    #hotspot_ids = DealStatus.objects.filter(deal__in=deals).values_list('beacon_id', flat=True).distinct().exclude(beacon__in=excluded_beacons).exclude(deal__in=excluded_deals)
    for week in range(0, number_of_weeks):
        today = start_date - timedelta(weeks=week)
        last_week = start_date - timedelta(weeks=week + 1)
        #two_weeks_ago = start_date - timedelta(weeks=week + 2)
        weekly_users = Location.objects.filter(date_created__gte=last_week, date_created__lt=today, user__in=user_qs).values_list('user', flat=True).distinct()
        total_users_to_date = get_users_with_redemptions(user_qs, today)
        total_users_last_week = get_users_with_redemptions(user_qs, last_week)
        new_users_this_week = len(total_users_to_date) - len(total_users_last_week)
        percentage_increase = new_users_this_week/float(len(total_users_last_week))
        #hotspots = Beacon.objects.filter(pk__in=hotspot_ids, date_created__lt=today, date_created__gte=last_week).exclude(cancelled=True)
        contact_statuses = filter_contact_status_by_referrer(total_users_to_date, today, datetime(2014, 9, 1))
        viral_registrations = get_contact_status_registration(contact_statuses)
        additional_promo_code_registrations = get_promo_code_registrations_for_redeemers(weekly_users, datetime(2014, 9, 1), today, viral_registrations)
        registrations = viral_registrations + additional_promo_code_registrations
        new_users_from_viral = total_users_to_date.filter(pk__in=[x.pk for x in registrations]).exclude(pk__in=[x.pk for x in total_users_last_week])
        viral_growth = (len(new_users_from_viral)/float(len(total_users_last_week)))
        redemptions = redemption_qs.filter(user__in=weekly_users, date_created__lt=today, date_created__gte=last_week)
        #paid_deal_statuses = DealStatus.objects.filter(beacon__in=hotspots)
        paid_redemptions = len(redemptions.filter(deal_status=DEAL_STATUS.REDEEMED).exclude(payment_authorization="REWARD"))
        reward_redemptions = len(redemptions.filter(payment_authorization="REWARD", deal_status=DEAL_STATUS.REDEEMED))
        #total_redemptions = paid_redemptions + reward_redemptions
        revenue_this_week = 0
        power_redeemers = get_active_power_redeemers(seattle_users, 2, 30, today)
        for deal_status in redemptions:
            if deal_status.payment:
                if deal_status.payment.is_submitted:
                    revenue_this_week = revenue_this_week + deal_status.deal.item_price
        low_gross_profect_projection, high_gross_profit_projection = get_gross_profit(redemption_qs, today)
        # percent_open_radius = get_percent_open_radius(lat, lng, today, last_week)
        # users_with_follows = get_users_with_follows(today)
        # if len(users_with_follows):
        #     average_follows_per_user = len(Favorites.objects.filter(active=True, user_id__in=users_with_follows))/float(len(users_with_follows))
        # else:
        #     average_follows_per_user = 0
        print "Weekly Actives: " + str(len(weekly_users))
        print "Weekly Actives Without New Users: " + str(len(weekly_users) - new_users_this_week)
        print "Total User Percentage Increase: " + str(percentage_increase)
        print "(Viral) Registration: " + str(len(new_users_from_viral))
        print "Viral Growth: " + str(viral_growth)
        # print "Invitations/Hotspot: " + str(invitation_per_hotspot)
        print "Paid Redemptions: " + str(paid_redemptions)
        print "Reward Redemptions: " + str(reward_redemptions)
        print "Total Redemptions: " + str(len(redemptions))
        # print "Hotspots Set: " + str(len(hotspots))
        print "Power redeemers (>=2 in 30 days): " + str(len(power_redeemers))
        print "Total users: " + str(len(total_users_to_date))
        print "Percent: " + str(float(len(weekly_users))/len(total_users_to_date))
        print "Percent without New Users: " + str(float(len(weekly_users) - new_users_this_week)/(len(total_users_to_date) - new_users_this_week))
        print "Low Gross Profit/Year/User: " + str(low_gross_profect_projection/float(len(total_users_to_date)))
        print "High Gross Profit/Year/User: " + str(high_gross_profit_projection/float(len(total_users_to_date)))
        print "Revenue: " + str(revenue_this_week)
        print "Projected ARPU: " + str((revenue_this_week * 52)/float(len(total_users_to_date)))
        print "Average Friends/User: "  + str(get_average_number_of_friends_on_hotspot(total_users_to_date))
        print ""


def redeemer_stats(start_date=datetime.now(), number_of_weeks=10):
    seattle_users = get_user_within_distance(sea_lat, sea_lng, large_radius)
    user_qs = get_users_with_redemptions(seattle_users)
    redemption_qs = get_redemptions_without_duplicates(user_qs, redemption_analytics_cutoff_date, start_date)
    #venues = active_and_inactive_seattle_venues
    #deals = Deal.objects.filter(place__in=venues, active=True, in_app_payment=True)
    #users_in_distance = User.objects.filter(pk__in=[x.pk for x in users])
    #user_qs = get_users_with_redemptions(users_in_distance, datetime.now())
    #excluded_beacons = Beacon.objects.filter(creator_id__in=excluded_users)
    #hotspot_ids = DealStatus.objects.filter(deal__in=deals).values_list('beacon_id', flat=True).distinct().exclude(beacon__in=excluded_beacons).exclude(deal__in=excluded_deals)
    for week in range(0, number_of_weeks):
        today = start_date - timedelta(weeks=week)
        last_week = start_date - timedelta(weeks=week + 1)
        #two_weeks_ago = start_date - timedelta(weeks=week + 2)
        weekly_users = Location.objects.filter(date_created__gte=last_week, date_created__lt=today, user__in=user_qs).values_list('user', flat=True).distinct()
        total_users_to_date = get_users_with_redemptions(user_qs, today)
        total_users_last_week = get_users_with_redemptions(user_qs, last_week)
        new_users_this_week = len(total_users_to_date) - len(total_users_last_week)
        percentage_increase = new_users_this_week/float(len(total_users_last_week))
        #hotspots = Beacon.objects.filter(pk__in=hotspot_ids, date_created__lt=today, date_created__gte=last_week).exclude(cancelled=True)
        contact_statuses = filter_contact_status_by_referrer(total_users_to_date, today, datetime(2014, 9, 1))
        viral_registrations = get_contact_status_registration(contact_statuses)
        additional_promo_code_registrations = get_promo_code_registrations_for_redeemers(weekly_users, datetime(2014, 9, 1), today, viral_registrations)
        registrations = viral_registrations + additional_promo_code_registrations
        new_users_from_viral = total_users_to_date.filter(pk__in=[x.pk for x in registrations]).exclude(pk__in=[x.pk for x in total_users_last_week])
        viral_growth = (len(new_users_from_viral)/float(len(total_users_last_week)))
        redemptions = redemption_qs.filter(date_created__lt=today, date_created__gte=last_week)
        #paid_deal_statuses = DealStatus.objects.filter(beacon__in=hotspots)
        paid_redemptions = len(redemptions.filter(deal_status=DEAL_STATUS.REDEEMED).exclude(payment_authorization="REWARD"))
        reward_redemptions = len(redemptions.filter(payment_authorization="REWARD", deal_status=DEAL_STATUS.REDEEMED))
        #total_redemptions = paid_redemptions + reward_redemptions
        revenue_this_week = 0
        power_redeemers = get_active_power_redeemers(seattle_users, 2, 30, today)
        for deal_status in redemptions:
            if deal_status.payment:
                if deal_status.payment.is_submitted:
                    revenue_this_week = revenue_this_week + deal_status.deal.item_price
        low_gross_profect_projection, high_gross_profit_projection = get_gross_profit(redemption_qs, today)
        # percent_open_radius = get_percent_open_radius(lat, lng, today, last_week)
        # users_with_follows = get_users_with_follows(today)
        # if len(users_with_follows):
        #     average_follows_per_user = len(Favorites.objects.filter(active=True, user_id__in=users_with_follows))/float(len(users_with_follows))
        # else:
        #     average_follows_per_user = 0
        print "Weekly Actives: " + str(len(weekly_users))
        print "Weekly Actives Without New Users: " + str(len(weekly_users) - new_users_this_week)
        print "Total User Percentage Increase: " + str(percentage_increase)
        print "(Viral) Registration: " + str(len(new_users_from_viral))
        print "Viral Growth: " + str(viral_growth)
        # print "Invitations/Hotspot: " + str(invitation_per_hotspot)
        print "Paid Redemptions: " + str(paid_redemptions)
        print "Reward Redemptions: " + str(reward_redemptions)
        print "Total Redemptions: " + str(len(redemptions))
        # print "Hotspots Set: " + str(len(hotspots))
        print "Power redeemers (>=2 in 30 days): " + str(len(power_redeemers))
        print "Total users: " + str(len(total_users_to_date))
        print "Percent: " + str(float(len(weekly_users))/len(total_users_to_date))
        print "Percent without New Users: " + str(float(len(weekly_users) - new_users_this_week)/(len(total_users_to_date) - new_users_this_week))
        print "Gross Profit Projection: " + str(high_gross_profit_projection)
        print "Gross Profit/Year/User Projection: " + str(high_gross_profit_projection/float(len(total_users_to_date)))
        print "Revenue: " + str(revenue_this_week)
        print "Projected ARPU: " + str((revenue_this_week * 52)/float(len(total_users_to_date)))
        print "Average Friends/User: "  + str(get_average_number_of_friends_on_hotspot(total_users_to_date))
        print ""


def get_gross_profit(redemptions, today):
    min_date = today - timedelta(weeks=4)
    redemptions = redemptions.filter(date_created__lt=today, date_created__gte=min_date)
    paid_redemptions = redemptions.exclude(payment_authorization="REWARD")
    reward_redemptions = redemptions.filter(payment_authorization="REWARD")
    filtered_reward_redemptions = []
    for redemption in reward_redemptions:
        if DealStatus.objects.filter(user=redemption.user, date_created__lt=redemption.date_created, deal_status=DEAL_STATUS.REDEEMED).exists():
            filtered_reward_redemptions.append(redemption)
    low_gross_profit = (len(paid_redemptions) * 13)
    print "REWARD: " + str(len(filtered_reward_redemptions))
    print "PAID: " + str(len(paid_redemptions))
    print "TOTAL: " + str(len(paid_redemptions) + len(filtered_reward_redemptions))
    high_gross_profit = (len(paid_redemptions) + len(filtered_reward_redemptions)) * 13
    return low_gross_profit, high_gross_profit


def get_users_with_follows(today):
    users_with_follows = []
    users = Favorites.objects.filter(active=True, date_updated__lte=today).distinct('user').exclude(user_id__in=excluded_users).values_list('user', flat=True)
    users_qs = User.objects.filter(pk__in=users)
    for user in users_qs:
        user_favorites = Favorites.objects.filter(user=user, active=True)
        user_redemptions = DealStatus.objects.filter(user=user, deal_status=DEAL_STATUS.REDEEMED).distinct('deal')
        if (len(user_favorites) - len(user_redemptions)) > 0:
            users_with_follows.append(user)
    return users_with_follows


def get_promo_code_registrations(last_week, today, users_to_exclude):
    acceptable_promo_codes = Promo.objects.filter(referring_user__isnull=False, item_number=1).values_list('promo_code', flat=True)
    user_ids = RewardItem.objects.filter(promo_code__in=acceptable_promo_codes, date_created__gte=last_week, date_created__lt=today).values_list('user', flat=True)
    users = User.objects.filter(pk__in=user_ids).exclude(pk__in=excluded_users).exclude(pk__in=[x.pk for x in users_to_exclude])
    return users


def get_promo_code_registrations_for_redeemers(users, last_week, today, users_to_exclude):
    acceptable_promo_codes = Promo.objects.filter(referring_user__in=users, item_number=1).values_list('promo_code', flat=True)
    new_redeemers = users.values_list('pk', flat=True)
    user_ids = RewardItem.objects.filter(promo_code__in=acceptable_promo_codes, date_created__gte=last_week, date_created__lt=today).values_list('user', flat=True)
    users = User.objects.filter(pk__in=user_ids).filter(pk__in=new_redeemers).exclude(pk__in=excluded_users).exclude(pk__in=[x.pk for x in users_to_exclude])
    return list(users)


def get_converted_users(users, date):
    braintree.Configuration.configure(
        braintree.Environment.Production,
        'c9zkknmmybm6778w',
        '8xcmpngmd5wgkm99',
        'e3a83a606ee128985268f6c46deb9a8a'
    )

    converted_users = []
    for user in users:
        try:
            customer = braintree.Customer.find(str(user.id))
            if len(customer.payment_sources) > 0:
                converted_users.append(customer)
        except:
            pass
    return converted_users


def get_percent_open_radius(latitude, longitude, max_date, min_date, radius=0.5):
    lat_range = [latitude-0.3, latitude+0.3]
    lng_range = [longitude-0.3, longitude+0.3]
    venues = get_venues_within_distance(latitude, longitude, large_radius)
    # filtered_venue_ids = Deal.objects.filter(place__in=all_venues, active=True, in_app_payment=True).values_list('place_id', flat=True)
    # venues = DealPlace.objects.filter(pk__in=filtered_venue_ids)
    locations = Location.objects.filter(latitude__range=lat_range, longitude__range=lng_range, date_created__range=[min_date, max_date]).exclude(user__in=excluded_users).distinct('latitude')
    locations_within_radius = []
    for location in locations:
        if location_within_radius(location, venues, radius):
            locations_within_radius.append(location)
    return len(locations_within_radius)/float(len(locations))


def get_locations_outside_radius(latitude, longitude, max_date, min_date, radius=0.5):
    lat_range = [latitude-0.3, latitude+0.3]
    lng_range = [longitude-0.3, longitude+0.3]
    venues = get_venues_within_distance(latitude, longitude, large_radius)
    # filtered_venue_ids = Deal.objects.filter(place__in=all_venues, active=True, in_app_payment=True).values_list('place_id', flat=True)
    # venues = DealPlace.objects.filter(pk__in=filtered_venue_ids)
    locations = Location.objects.filter(latitude__range=lat_range, longitude__range=lng_range, date_created__range=[min_date, max_date]).exclude(user__in=excluded_users).distinct('latitude')
    locations_outside_radius = []
    for location in locations:
        if not location_within_radius(location, venues, radius):
            locations_outside_radius.append(location)
    return locations_outside_radius


def location_within_radius(location, venues, radius):
    for venue in venues:
        distance = distance_between_two_points(venue.latitude, venue.longitude, location.latitude, location.longitude)
        if distance < radius:
            return True
    return False

#vesitigial (double check)
def get_hotspots_set(min_date, max_date):
    venues = DealPlace.objects.all()
    deals = Deal.objects.filter(place__in=venues)
    beacons = Beacon.objects.all().exclude(creator__in=excluded_users)
    unique_deal_statuses = DealStatus.objects.filter(deal__in=deals, beacon__in=beacons, date_created__gte=min_date, contact=None, date_created__lte=max_date).distinct("beacon")
    return unique_deal_statuses


def contact_status_breakdown(contact_statuses):
    contact_status_qs = ContactStatus.objects.filter(pk__in=[x.id for x in contact_statuses])
    hotspot_invites = contact_status_qs.filter(deal_status__isnull=False)
    hotspot_invite_reg = hotspot_invites.filter(installed_app=True)
    app_invites = contact_status_qs.filter(contact__isnull=False)
    app_invite_reg = app_invites.filter(installed_app=True)
    web_invites = contact_status_qs.filter(phone_number__isnull=False)
    web_invite_reg = web_invites.filter(installed_app=True)
    print "Total Hotspot Invites: " + str(len(hotspot_invites))
    print "Reg from Hotspot Invites: " + str(len(hotspot_invite_reg))
    print "Hotspot Invite Conversion: " + str(len(hotspot_invite_reg)/float(len(hotspot_invites)))
    print ""
    print "Total App Invites: " + str(len(app_invites))
    print "Reg from App Invites: " + str(len(app_invite_reg))
    print "App Invite Conversion: " + str(len(app_invite_reg)/float(len(app_invites)))
    print ""
    print "Total Web Invites: " + str(len(web_invites))
    print "Reg from Web Invites: " + str(len(web_invite_reg))
    print "Web Invite Conversion: " + str(len(web_invite_reg)/float(len(web_invites)))
    print ""


def seattle_users_ios(min_date=datetime(2013, 1, 1), max_date=datetime.now()):
    seattle_users = get_user_within_distance(sea_lat, sea_lng, large_radius)
    android_user_ids = AndroidDevice.objects.all().values_list('user', flat=True)
    seattle_user_qs = User.objects.filter(pk__in=[x.pk for x in seattle_users], date_joined__range=[min_date, max_date]).exclude(pk__in=android_user_ids)
    return seattle_user_qs


def get_inactives(min_date=(datetime.now() - timedelta(weeks=1)), max_date=datetime.now()):
    seattle_user_qs = seattle_users_ios()
    weekly_locations = Location.objects.filter(date_created__gte=min_date, date_created__lt=max_date, user__in=seattle_user_qs).values_list('user', flat=True).distinct()
    active_users = User.objects.filter(pk__in=weekly_locations)
    inactive_users = []
    for x in seattle_user_qs:
        if x not in active_users:
            inactive_users.append(x)
    return inactive_users


def followers_wo_redemption(user_set):
    redeemers = users_w_redemptions(user_set)
    follows = Favorites.objects.filter(user__in=user_set, active=True).distinct('user').values_list('user', flat=True)
    followers = User.objects.filter(pk__in=follows)
    followers_wo_redemption = set(followers).difference(redeemers)
    return followers_wo_redemption


def retention_stats(users):
    #create dict for active and total users on x day/week/month after joining
    day_points = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 21, 30, 45, 60, 75, 90]
    dau_stats = {}
    for i in day_points:
        dau_stats[i] = {'total': [], 'active': []}
    week_points = [x for x in range(1,13)]
    wau_stats = {}
    for i in week_points:
        wau_stats[i] = {'total': [], 'active': []}
    month_points = [1,2,3]
    mau_stats = {}
    for i in month_points:
        mau_stats[i] = {'total': [], 'active': []}
    #declares how many total days after joining the user has existed (tot_days) and lists for which days, weeks, and months after joining they were active
    for user in users:
        join_date = user.date_joined.date()
        today = (datetime.now()).date()
        tot_days = (today - join_date).days
        days_after = []
        weeks_after = []
        months_after = []
        locations = Location.objects.filter(user=user)
        #adds to days/weeks/months_after list if user was active
        for x in locations:
            day = x.date_created.date()
            day_after = (day - join_date).days
            if day_after not in days_after:
                days_after.append(day_after)
            week_after = day_after/7
            if week_after not in weeks_after:
                weeks_after.append(week_after)
            month_after = day_after/30
            if month_after not in months_after:
                months_after.append(month_after)
        #adds user to dau/wau/mau dict for every day/week/month after joining they were active or existed
        for i in day_points:
            if i <= tot_days:
                dau_stats[i]["total"].append(user)
            if i in days_after:
                dau_stats[i]["active"].append(user)
        for i in week_points:
            if i <= tot_days/7:
                wau_stats[i]["total"].append(user)
            if i in weeks_after:
                wau_stats[i]["active"].append(user)
        for i in month_points:
            if i <= tot_days/30:
                mau_stats[i]["total"].append(user)
            if i in months_after:
                mau_stats[i]["active"].append(user)
    #print out
    print "dau stats"
    print "day, ratio, tot, active"
    for i in day_points:
        active = len(dau_stats[i]["active"]) + 0.0
        tot = len(dau_stats[i]["total"]) + 0.0
        if tot > 0:
            ratio = active/tot
            print "{0}, {1}, {2}, {3}".format(i, ratio, tot, active)
    print " "
    print"wau_stats"
    for i in week_points:
        active = len(wau_stats[i]["active"]) + 0.0
        tot = len(wau_stats[i]["total"]) + 0.0
        if tot > 0:
            ratio = active/tot
            print "{0}, {1}, {2}, {3}".format(i, ratio, tot, active)
    print " "
    print"mau_stats"
    for i in month_points:
        active = len(mau_stats[i]["active"]) + 0.0
        tot = len(mau_stats[i]["total"]) + 0.0
        if tot > 0:
            ratio = active/tot
            print "{0}, {1}, {2}, {3}".format(i, ratio, tot, active)
    print " "

def get_notifications_by_venue(venue, min_date=(datetime.now() - timedelta(days=30)), max_date=datetime.now()):
    notifications_by_venue = NotificationTracker.objects.filter(date_created__gte=min_date, date_created__lt=max_date, notification_type=NOTIFICATION_TYPE.FRIEND_INVITED_PUSH, notification_detail__contains=venue.name).exclude(sender__in=excluded_users)
    return notifications_by_venue

def get_page_views_by_venue(venue, min_date=(datetime.now() - timedelta(days=30)), max_date=datetime.now()):
    views = ViewTracker.objects.filter(date_created__gte=min_date, date_created__lt=max_date, view_id=venue.id).exclude(user__in=excluded_users)
    unique_viewers = views.values_list('user').distinct()
    return views, unique_viewers

def venue_stats(min_date=(datetime.now() - timedelta(days=30)), max_date=datetime.now()):
    #seattle_users = get_user_within_distance(sea_lat, sea_lng, large_radius)
    #active_seattle_venues = get_venues_within_distance(sea_lat, sea_lng, large_radius,active_only=True)
    #all_redemptions = get_redemptions(seattle_users,min_date, max_date)
    active_deal_places = Deal.objects.filter(in_app_payment=True,active=True).values_list('place',flat=True)
    active_seattle_venues = DealPlace.objects.filter(pk__in=active_deal_places)
    all_redemptions = DealStatus.objects.filter(deal_status="R",date_created__gte=min_date,date_created__lt=max_date).exclude(user__in=excluded_users).exclude(deal__in=excluded_deals)
    print "From {0} to {1}: {2} total redemptions".format(min_date.date(), max_date.date(), str(len(all_redemptions)))
    print "venue, tot_redemptions, paid_redemptions, amt owed, public_checkins, notifications, followers"
    for venue in active_seattle_venues:
        deals = Deal.objects.filter(place=venue)
        deal_statuses = DealStatus.objects.filter(deal__in=deals, date_created__gte=min_date, date_created__lt=max_date).exclude(user__in=excluded_users).exclude(deal__in=excluded_deals)
        public_checkins = deal_statuses.filter(public=True)
        tot_redemptions = deal_statuses.filter(deal_status=DEAL_STATUS.REDEEMED)
        paid_redemptions = tot_redemptions.exclude(payment_authorization="REWARD")
        notifications_sent = get_notifications_by_venue(venue, min_date, max_date)
        favorites = Favorites.objects.filter(place=venue, active=True)
        unique_followers = favorites.values_list('user').distinct()
        #page_views, unique_viewers = get_page_views_by_venue(venue, min_date, max_date)
        revenue = 0
        for deal in deals:
            items = tot_redemptions.filter(deal=deal)
            revenue = revenue + (len(items) * deal.item_cost)
        print venue.name + ", {0}, {1}, ${2}, {3}, {4}, {5}".format(len(tot_redemptions), len(paid_redemptions), str(revenue), len(public_checkins), len(notifications_sent), len(unique_followers))

promo_dct = {
    'drinksea': {'venue_id': 29704, 'name': 'Coasters', 'contact': 'Coasters'},
    'seattlebg3': {'venue_id': 91, 'name': 'Denise Kathleen', 'contact': 'denisekathleen78@gmail.com'},
    'seattleba4': {'venue_id': 19983, 'name': 'Tim Hotchkin', 'contact': 'djmot67@gmail.com'},
    'kessler1': {'venue_id': 91, 'name': 'Denise Kathleen', 'contact': 'denisekathleen78@gmail.com'},
    'kessler2': {'venue_id': 91, 'name': 'Tracy Ward', 'contact': '555kess@gmail.com'},
    'kessler3': {'venue_id': 91, 'name': 'Keo Colorado', 'contact': 'dwntwnkeo@gmail.com'},
    '500east': {'venue_id': 29704, 'name': 'Zach Shore (team)', 'contact': 'zshore221@gmail.com'},
    'lloydmartin': {'venue_id': 29498, 'name': 'Jennifer Selden (team)', 'contact': 'jennifer.nwls@gmail.com'},
    'wsbowl': {'venue_id': 20383, 'name': 'Jeff Swanson (team)', 'contact': 'jeffs@wsbowl.com'},
    'westbowl': {'venue_id': 20383, 'name': 'Jeff Swanson (team)', 'contact': 'jeffs@wsbowl.com'},
    'coterie': {'venue_id': 35233, 'name': 'Su-zette Sparks (team)', 'contact': 'suzette@coterieworklounge.com'},
    'seattlea4': {'venue_id': 29651, 'name': 'Hilliards (team)', 'contact': 'aleko@hilliardsbeer.com'},
    'seattlea2': {'venue_id': 20689, 'name': 'Kate Strang', 'contact': 'kate_strang@live.com'},
    'thegeorge1': {'venue_id': 20689, 'name': 'Kate Strang', 'contact': 'kate_strang@live.com'},
    'thegeorge2': {'venue_id': 20689, 'name': 'Mary', 'contact': 'mevelelynmac@gmail.com'},
    'thegeorge3': {'venue_id': 20689, 'name': 'UNCLAIMED', 'contact': 'tbd'},
    'roxys1': {'venue_id': 29523, 'name': 'UNCLAIMED', 'contact': 'tbd'},
    'roxys2': {'venue_id': 29523, 'name': 'UNCLAIMED', 'contact': 'tbd'},
    'buckley1': {'venue_id': 20569, 'name': 'UNCLAIMED (belltown)', 'contact': 'tbd'},
    'buckley2': {'venue_id': 20569, 'name': 'UNCLAIMED (belltown)', 'contact': 'tbd'},
    'buckley3': {'venue_id': 20569, 'name': 'UNCLAIMED (belltown)', 'contact': 'tbd'},
    'buckley4': {'venue_id': 20569, 'name': 'UNCLAIMED (belltown)', 'contact': 'tbd'},
    'buckley5': {'venue_id': 20569, 'name': 'UNCLAIMED (belltown)', 'contact': 'tbd'},
    'seattlebg1': {'venue_id': 102, 'name': 'Sam Sparks', 'contact': 'samjsparks@yahoo.com'},
    'seattlebg2': {'venue_id': 102, 'name': 'Sarah Dennis', 'contact': 'sarahdennis1@outlook.com'},
    'seattlebg4': {'venue_id': 102, 'name': 'Ross McCartney', 'contact': '2062343087'},
    'changes1': {'venue_id': 93, 'name': 'UNCLAIMED', 'contact': 'NA'},
    'changes2': {'venue_id': 93, 'name': 'UNCLAIMED', 'contact': 'NA'},
    'changes3': {'venue_id': 93, 'name': 'UNCLAIMED', 'contact': 'NA'},
    'changes4': {'venue_id': 93, 'name': 'UNCLAIMED', 'contact': 'NA'},
    'seattlepie1': {'venue_id': 113, 'name': 'Kelly Patrick', 'contact': 'Kellyy.kpat@gmail.com'},
    'seattlepie2': {'venue_id': 113, 'name': 'UNCLAIMED', 'contact': 'NA'},
    'seattlepie3': {'venue_id': 113, 'name': 'UNCLAIMED', 'contact': 'NA'},
    'seattlepie4': {'venue_id': 113, 'name': 'Robin LaChance', 'contact': 'winddancer78@hotmail.com'},
    'ballroom1': {'venue_id': 100, 'name': 'Cynthia Huntley', 'contact': 'cynthia3614@gmail.com'},
    'ballroom2': {'venue_id': 100, 'name': 'TBD', 'contact': 'TBD', 'users': [], 'redemptions':[]},
    'seattlebl1': {'venue_id': 100, 'name': 'Tamara Rose', 'contact': 'tamara@ballroomfremont.com'},
    'seattlebl2': {'venue_id': 100, 'name': 'Collette Kitchell', 'contact': 'collettekitchell@aol.com'},
    'seattlebl3': {'venue_id': 100, 'name': 'Nate Thomas', 'contact': 'Nathaniell.thomas@gmail.com'},
    'seattlebl4': {'venue_id': 100, 'name': 'Cynthia Huntley', 'contact': 'cynthia3614@gmail.com'},
    'seattlebl5': {'venue_id': 100, 'name': 'Collette Kitchell (2nd set)', 'contact': 'collettekitchell@aol.com'},
    'seattlebl6': {'venue_id': 100, 'name': 'Jake Cabrales', 'contact': 'jcab81@gmail.com'},
    'seattlebl7': {'venue_id': 100, 'name': 'Drew Kurata', 'contact': 'kurata_13@hotmail.com'},
    'seattleba1': {'venue_id': 100, 'name': 'UNCLAIMED', 'contact': 'NA'},
    'seattleba2': {'venue_id': 100, 'name': 'UNCLAIMED', 'contact': 'NA'},
    'seattleba3': {'venue_id': 100, 'name': 'UNCLAIMED', 'contact': 'NA'},
    'clever1': {'venue_id': 115, 'name': 'UNCLAIMED', 'contact': 'NA'},
    'clever2': {'venue_id': 115, 'name': 'UNCLAIMED', 'contact': 'NA'},
    'clever3': {'venue_id': 115, 'name': 'UNCLAIMED', 'contact': 'NA'},
    'clever4': {'venue_id': 115, 'name': 'UNCLAIMED', 'contact': 'NA'}
}

def get_drink_card_stats(min_date=(datetime.now() - timedelta(weeks=1)), max_date=datetime.now()):
    print "From {0} to {1}".format(min_date.date(), max_date.date())
    target_promos = promo_dct.keys()
    drink_card_users = get_drink_card_users(target_promos)
    users_with_redemptions = get_users_with_redemptions(drink_card_users, max_date, min_date)
    drink_card_payouts = {}
    for user in users_with_redemptions:
        reward_item = RewardItem.objects.get(user=user, promo_code__in=promo_dct.keys())
        promo_code = reward_item.promo_code
        #redemptions = get_redemptions([user], reward_item.date_created)
        first_redemption = DealStatus.objects.filter(date_created__gte=reward_item.date_created, deal_status=DEAL_STATUS.REDEEMED).order_by('date_created')[0]
        if min_date < first_redemption.date_created < max_date:
            if promo_code in drink_card_payouts.keys():
                drink_card_payouts[promo_code].append(user)
            else:
                drink_card_payouts[promo_code] = [user]
    print "code, venue, newly activated users, name, contact"
    for key, value in drink_card_payouts.iteritems():
        users_with_promo = get_drink_card_users([key])
        users_in_period = users_with_promo.filter(date_joined__gte=min_date, date_joined__lt=max_date)
        venue = DealPlace.objects.get(id=promo_dct[key]["venue_id"])
        print key + ", " + venue.name + ", " + str(len(value)) + " activations, " + str(len(users_in_period)) + " users joined," + promo_dct[key]["name"] + ", " + promo_dct[key]["contact"]


def get_drink_card_users(target_promos):
    reward_items = RewardItem.objects.filter(promo_code__in=target_promos)
    drink_card_users = User.objects.filter(pk__in=[x.user.id for x in reward_items]).exclude(pk__in=excluded_users)
    return drink_card_users


def get_deal_hours(id):
    place = DealPlace.objects.get(id=id)
    print place
    deal = Deal.objects.get(place=place)
    hours = DealHours.objects.filter(deal=deal)
    print hours
    return hours


from beaconWeb.apps.beacon.common.constants.notification_types import NOTIFICATION_TYPE


def get_notifications_per_redemption(min_date, max_date, deal_statuses):
    return True


def get_average_number_of_friends_on_hotspot(users):
    users = User.objects.filter(pk__in=[x.id for x in users]).exclude(pk__in=excluded_users)
    user_phone_numbers = Contact.objects.filter(user__in=users).values_list('normalized_phone', flat=True)
    user_friends = User.objects.filter(username__in=user_phone_numbers)
    average_friends = float(len(user_friends))/len(users)
    return average_friends


def user_received_social_notification():
    has_device = ~(Q(ios_devices=None) & Q(android_devices=None))
    recipient_ids = NotificationTracker.objects.filter(notification_type=NOTIFICATION_TYPE.FRIEND_INVITED_PUSH).values_list('recipient', flat=True)
    users_with_notification = User.objects.filter(pk__in=recipient_ids).filter(has_device)


def social_notification_performance():
    return True


def redemption_times(venues, min_date=redemption_analytics_cutoff_date, max_date=datetime.now() - timedelta(seconds=1)):
    print "From {0} to {1}".format(min_date.date(), max_date.date())
    seattle_users = get_user_within_distance(sea_lat, sea_lng, large_radius)
    all_redemptions = get_redemptions(seattle_users, min_date, max_date)
    redemptions = all_redemptions.filter(deal__place__in=venues)
    times = []
    for r in redemptions:
        rtime = r.date_created - timedelta(hours=2)
        times.append(rtime)
    day_dct = {}
    hour_dct = {}
    both_dct = {}
    for day in range(1,8):
        day_dct[day] = []
        both_dct[day] = {}
        for hour in range(24):
            both_dct[day][hour] = []
    for hour in range(24):
        hour_dct[hour] = []
    for t in times:
        day = t.isoweekday()
        hour = t.hour
        day_dct[day].append(t)
        hour_dct[hour].append(t)
        both_dct[day][hour].append(t)
    print "\nBy day"
    weekdays = {1:"Mon", 2:"Tue", 3:"Wed", 4:"Thu", 5:"Fri", 6:"Sat", 7:"Sun"}
    for day in day_dct:
        today = weekdays[day]
        print "{0}, {1}".format(today, str(len(day_dct[day])))
    print "\nBy hour"
    for hour in hour_dct:
        if len(hour_dct[hour]) > 0:
            print "{0} - {1}, {2}".format(str(hour), str(hour+1), str(len(hour_dct[hour])))
    print "\nTotal distribution"
    for day in both_dct:
        today = weekdays[day]
        for hour in both_dct[day]:
            if len(hour_dct[hour]) > 0:
                print "{0} {1} - {2}, {3}".format(today, str(hour), str(hour+1), str(len(both_dct[day][hour])))


def redemptions_by_venue(min_date=redemption_analytics_cutoff_date, max_date=datetime.now() - timedelta(seconds=1)):
    venues = get_venues_within_distance(47.66759, -122.312766, 20)
    print "From {0} to {1}".format(min_date.date(), max_date.date())
    print "venue, tot_redemptions, price, item, deal_date_created, redemptions_per_week, paid_redemptions, paid_ratio, followers"
    for venue in venues:
        deals = Deal.objects.filter(place=venue)
        active_deal = Deal.objects.filter(place=venue, active=True)[0]
        deal_price = active_deal.item_price
        deal_item = active_deal.item_name
        deal_date_created = active_deal.date_created.strftime("%Y-%m-%d")
        #time_since_deal_creation = datetime.now() - active_deal.date_created
        if max_date < active_deal.date_created:
            time_since = max_date - min_date
        else:
            time_since = max_date - active_deal.date_created
        days_since = time_since.days/1.0
        weeks_since = days_since/7.0
        #public_checkins = deal_statuses.filter(public=True)
        deal_statuses = DealStatus.objects.filter(deal__in=deals, date_created__gte=min_date, date_created__lt=max_date).exclude(user__in=excluded_users).exclude(deal__in=excluded_deals)
        tot_redemptions = deal_statuses.filter(deal_status=DEAL_STATUS.REDEEMED)
        paid_redemptions = tot_redemptions.exclude(payment_authorization="REWARD")
        if len(tot_redemptions) > 0:
            num_redemptions = len(tot_redemptions)/1.0
            paid_ratio = round(len(paid_redemptions)/num_redemptions, 2)
        else:
            paid_ratio = 0
        if weeks_since >=1:
            redemptions_per_week = round(len(tot_redemptions)/weeks_since, 2)
        else:
            redemptions_per_week = 0
        favorites = Favorites.objects.filter(place=venue, active=True)
        unique_followers = favorites.values_list('user').distinct()
        #revenue = 0
        #for deal in deals:
            #items = tot_redemptions.filter(deal=deal)
            #revenue = revenue + (len(items) * deal.item_cost)
        print venue.name + ", {0}, {1}, {2}, {3}, {4}, {5}, {6}, {7}".format(len(tot_redemptions), str(deal_price), deal_item, deal_date_created, str(redemptions_per_week), len(paid_redemptions), str(paid_ratio), len(unique_followers))


def get_redemption_segments(users, min_date=redemption_analytics_cutoff_date, max_date=datetime.now() - timedelta(seconds=1)):
    segments_dct = {}
    users_dct = {}
    #redemptions = DealStatus.objects.filter(user__in=users, deal_status=DEAL_STATUS.REDEEMED, date_created__gte=min_date, date_created__lt=max_date).exclude(user__in=excluded_users).exclude(deal__in=excluded_deals)
    redemptions = get_redemptions_without_duplicates(users,min_date,max_date)
    #print str(len(redemptions))
    for x in redemptions:
        if x.user:
            redemption_date = x.date_created.strftime("%Y-%m-%d")
            if x.user not in users_dct.keys():
                users_dct[x.user] = [x]
            else:
                users_dct[x.user].append(x)
    for k, v in users_dct.iteritems():
        num_redemptions = len(users_dct[k])
        if num_redemptions not in segments_dct.keys():
            segments_dct[num_redemptions] = [k]
        else:
            segments_dct[num_redemptions].append(k)
    num_redemptions = len(redemptions)/1.0
    num_users_w_redemption = len(users_dct.keys())/1.0
    def ratio(x, y):
        r = x/y
        return r
    print str(num_redemptions) + " redemptions over " + str(num_users_w_redemption) + " users"
    print "Average: {0} redemptions/user".format(str(ratio(num_redemptions, num_users_w_redemption)))
    repeat_users = 0
    threepeat_users = 0
    for k, v in segments_dct.iteritems():
        num_users = len(v)
        if k >= 2:
            repeat_users += num_users
        if k >= 3:
            threepeat_users += num_users
        print str(k) + ", " + str(len(v)) + ", " + str(ratio(num_users, num_users_w_redemption))
    print "\nRepeat users: {0}, {1}".format(str(repeat_users), str(ratio(repeat_users, num_users_w_redemption)))
    print "Threepeat users: {0}, {1}".format(str(threepeat_users), str(ratio(threepeat_users, num_users_w_redemption)))
    return segments_dct


def users_for_feedback(users):
    android_user_ids = AndroidDevice.objects.all().values_list('user', flat=True)
    print "first_name, last_name, email, id, date_joined, OS, redemptions, contacts"
    for user in users:
        redemptions = DealStatus.objects.filter(user=user, deal_status=DEAL_STATUS.REDEEMED)
        contacts = Contact.objects.filter(user=user).values_list('normalized_phone', flat=True)
        num_friends = len(get_friends(user)[0])
        OS = "iOS"
        if user.id in android_user_ids:
            OS = "Android"
        print user.first_name + "," + user.last_name + "," + user.email + "," + str(user.id) + "," + str(user.date_joined) + "," + OS + ", " + str(len(redemptions)) + "," + str(num_friends)
    return users


def calculate_nps(responses):
    dectractors = responses.filter(nps_score__lte=6)
    passives = responses.filter(nps_score__range=(7,8))
    promoters = responses.filter(nps_score__gte=9)
    d = len(dectractors)/1.0
    p = len(promoters)/1.0
    r = len(responses)/1.0
    if r > 0:
        nps = (p - d)/r*100
    else:
        nps = 0
    nps_rounded = round(nps,2)
    return nps_rounded


def event_nps_stats(min_date=datetime.now() - timedelta(weeks=6),max_date=datetime.now()):
    events = SponsoredEvent.objects.filter(start__gte=min_date, start__lt=max_date).order_by('-start')
    attendees = EventStatus.objects.filter(event__in=events, status="R").exclude(user__in=excluded_users).values_list('user', flat=True)
    all_responses = UserFeedback.objects.filter(sponsored_event__in=events, user__in=attendees).distinct('user','sponsored_event')
    nps = calculate_nps(all_responses)
    print "{0} events with {1} attendees: {2} NPS from {3} responses".format(str(len(events)), str(len(attendees)), str(nps), str(len(all_responses)))
    for i in range(1,11):
        score_i = all_responses.filter(nps_score=i)
        if len(score_i)>0:
            print str(i) + ": " + str(len(score_i)) + " responses"
    print " "
    for event in events:
        responses = all_responses.filter(sponsored_event=event)
        if len(responses) > 0:
            nps = calculate_nps(responses)
            print "{0}: {1} over {2} responses".format(event.place.name, str(nps),str(len(responses)))
            for i in range(1,11):
                score_i = responses.filter(nps_score=i)
                if len(score_i)>0:
                    print str(i) + ": " + str(len(score_i)) + " responses"
            print " "

def print_event_feedback(min_date=datetime.now() - timedelta(weeks=1),max_date=datetime.now()):
    events = SponsoredEvent.objects.filter(start__gte=min_date, start__lt=max_date).order_by('-start')
    attendees = EventStatus.objects.filter(event__in=events, status="R").exclude(user__in=excluded_users).values_list('user', flat=True)
    all_responses = UserFeedback.objects.filter(sponsored_event__in=events, user__in=attendees).distinct('user','sponsored_event')
    for event in events:
        nps_responses = all_responses.filter(sponsored_event=event)
        detailed_responses = all_responses.filter(sponsored_event=event, question1__isnull=False)
        if len(detailed_responses) > 0:
            nps = calculate_nps(nps_responses)
            print "{0}: {1} over {2} responses".format(event.place.name, str(nps), str(len(nps_responses)))
            for response in detailed_responses:
                try:
                    print "{0} {1} {2}: NPS {3}".format(str(response.user.id),response.user.first_name, response.user.last_name, response.nps_score)
                except:
                    print "{0}: NPS {1}".format(str(response.user.id),response.nps_score)
                print response.question1
                print response.question2
                print response.question3
                print response.question4
                print " "


def print_positive_event_feedback(min_date=datetime.now() - timedelta(weeks=1),max_date=datetime.now()):
    events = SponsoredEvent.objects.filter(start__gte=min_date, start__lt=max_date).order_by('-start')
    attendees = EventStatus.objects.filter(event__in=events, status="R").exclude(user__in=excluded_users).values_list('user', flat=True)
    all_responses = UserFeedback.objects.filter(sponsored_event__in=events, user__in=attendees).distinct('user','sponsored_event')
    for event in events:
        nps_responses = all_responses.filter(sponsored_event=event)
        detailed_responses = all_responses.filter(sponsored_event=event, question1__isnull=False)
        if len(detailed_responses) > 0:
            nps = calculate_nps(nps_responses)
            print "{0}: {1} over {2} responses".format(event.place.name, str(nps), str(len(nps_responses)))
            for response in detailed_responses:
                if response.nps_score == 9 or response.nps_score == 10:
                    try:
                        print "{0} {1} {2}: NPS {3}".format(str(response.user.id),response.user.first_name, response.user.last_name, response.nps_score)
                    except:
                        print "{0}: NPS {1}".format(str(response.user.id),response.nps_score)
                    print response.question1
                    print response.question2
                    print response.question3
                    print response.question4
                    print " "



def print_feedback_source_and_frequency(min_date=datetime.now() - timedelta(weeks=1),max_date=datetime.now()):
    events = SponsoredEvent.objects.filter(start__gte=min_date, start__lt=max_date).order_by('-start')
    attendees = EventStatus.objects.filter(event__in=events, status="R").exclude(user__in=excluded_users).values_list('user', flat=True)
    responses = UserFeedback.objects.filter(sponsored_event__in=events, user__in=attendees).distinct('user','sponsored_event')
    q2 = {}
    q3 = {}
    for response in responses:
        if response.question2 not in q2.keys():
            q2[response.question2] = 1
        else:
            q2[response.question2] = q2[response.question2] + 1
        if response.question3 not in q3.keys():
            q3[response.question3] = 1
        else:
            q3[response.question3] = q3[response.question3] + 1
    print "Where did you hear about the event?"
    for k,v in q2.iteritems():
        print str(k) + ": " + str(v)
    print " "
    print "How often would you go?"
    for k, v in q3.iteritems():
        print str(k) + ": " + str(v)


def event_status_stats(event):
    all_statuses = EventStatus.objects.filter(event=event).exclude(user__in=excluded_users)
    paid = all_statuses.filter(payment__isnull=False).exclude(refund_authorization__isnull=False)
    unpaid = all_statuses.exclude(pk__in=paid)
    #presale_cutoff = event.start - timedelta(hours=18)
    #print "Presale cuttoff: {0}".format(presale_cutoff)
    for statuses in [paid,unpaid]:
        redemptions = statuses.filter(status="R")
        early = redemptions.filter(is_presale=True)
        day_of = redemptions.filter(is_presale=False)
        try:
            cash = CashPayment.objects.get(event=event).total
        except:
            cash = 0
        unredeemed = statuses.filter(status="U")
        interested = statuses.filter(status="I")
        no_selection = statuses.filter(status="N")
        tips = 0
        for status in statuses:
            if status.tip_amount:
                tips += status.tip_amount
        if statuses[0].payment is not None:
            print "Paid"
            print "redemptions: {0}".format(len(redemptions))
            print "  presale: {0}".format(len(early))
            print "  day-of: {0}".format(len(day_of))
            print "  cash: {0}".format(str(cash))
            print "unredeemed: {0}".format(len(unredeemed))
            print "interested: {0}".format(len(interested))
            print "no selection: {0}".format(len(no_selection))
            print "tips: ${0}".format(str(tips))
            print " "
        else:
            print "Unpaid or refunded"
            print "redemptions: {0}".format(len(redemptions))
            print "unredeemed: {0}".format(len(unredeemed))


def print_nps_respondents(min_date=datetime.now() - timedelta(weeks=4),max_date=datetime.now()):
    responses = UserFeedback.objects.filter(date_created__gte=min_date, date_created__lt=max_date).exclude(user__in=excluded_users)
    for response in responses:
        print "{0} {1}, {2} nps, {3}, {4}".format(response.user.first_name, response.user.last_name, str(response.nps_score), response.sponsored_event.place.name,response.user.email)


def get_estimated_revenue(unredeemed_attendees):
    revenue = 0
    for event_status in unredeemed_attendees:
        revenue = revenue + event_status.event.item_price
    return revenue


def get_registered_users(events):
    registered_users = []
    for event in events:
        users = get_user_within_distance(event.place.latitude, event.place.longitude, large_radius)
        registered_users.extend(users)
    return set(registered_users)


def event_stats(max_date=datetime.now(), min_date=datetime.now()-timedelta(weeks=4)):
    events = SponsoredEvent.objects.filter(start__gte=min_date, start__lte=max_date)
    unredeemed_attendees, redeemed_attendees = get_event_attendees(events, max_date, min_date)
    nps = ""
    revenue = get_estimated_revenue(unredeemed_attendees)
    estimated_gross_profit = ""
    registered_users = get_registered_users(events)
    print "Unredeemed Attendees: " + str(len(unredeemed_attendees))
    print "Redeemed Attendees :" + str(len(redeemed_attendees))
    print "Estimate Revenue: " + str(revenue)
    print "Total Registered Users: " + str(len(registered_users))


def get_event_numbers(facebook_id):
    event = SponsoredEvent.objects.get(facebook_event_id=facebook_id)
    e = EventStatus.objects.filter(event=event, status="U")
    x = EventStatus.objects.filter(event=event, status="R")
    print "Unredeemed " + str(len(e))
    print "Redeemed " + str(len(x))
    print "Total " + str(len(e) + len(x))


def get_venues_within_distance_for_events(lat, lng, radius=standard_radius):
    venues_within_distance = []
    lat_range = [lat - 0.3, lat + 0.3]
    lng_range = [lng - 0.3, lng + 0.3]
    venues = DealPlace.objects.filter(latitude__range=lat_range, longitude__range=lng_range)
    for venue in venues:
        distance = distance_between_two_points(lat, lng, venue.latitude, venue.longitude)
        if distance < radius:
            venues_within_distance.append(venue)
    return venues_within_distance


def get_nps_score(sponsored_events):
    responses = UserFeedback.objects.filter(sponsored_event__in=sponsored_events).exclude(user__in=excluded_users)
    nps = calculate_nps(responses)
    return nps


def get_nps_breakdown(sponsored_events):
    responses = UserFeedback.objects.filter(sponsored_event__in=sponsored_events).exclude(user__in=excluded_users)
    detractors = responses.filter(nps_score__lte=6)
    passives = responses.filter(nps_score__range=(7, 8))
    promoters = responses.filter(nps_score__gte=9)
    return promoters, passives, detractors


def get_revenue_from_event_statuses(event_statuses):
    revenue = 0
    for event_status in event_statuses:
        if not event_status.refund_authorization:
            if event_status.is_presale:
                revenue += event_status.event.presale_item_price
            else:
                revenue += event_status.event.item_price
            revenue += event_status.tip_amount
    return revenue


def get_revenue_from_event_statuses_without_refunds(event_statuses):
    revenue = 0
    for event_status in event_statuses:
        if event_status.is_presale:
            revenue += event_status.event.presale_item_price
        else:
            revenue += event_status.event.item_price
        revenue += event_status.tip_amount
    return revenue


def get_revenue_from_cash_payments(cash_payments):
    revenue = 0
    for payment in cash_payments:
        revenue += payment.total
    return revenue


def get_revenue_for_events(sponsored_events):
    event_statuses = EventStatus.objects.filter(event__in=sponsored_events)
    redeemed_revenue = get_revenue_from_event_statuses_without_refunds(event_statuses.filter(status=EVENT_STATUS.REDEEMED))
    unredeemed_revenue = get_revenue_from_event_statuses_without_refunds(event_statuses.filter(status=EVENT_STATUS.GOING))
    cash_revenue = get_revenue_from_cash_payments(CashPayment.objects.filter(event__in=sponsored_events))
    total_revenue = redeemed_revenue + unredeemed_revenue + cash_revenue
    return total_revenue, redeemed_revenue, unredeemed_revenue, cash_revenue


def get_tip_percentage(sponsored_events, revenue):
    event_statuses = EventStatus.objects.filter(event__in=sponsored_events)
    tips = 0
    for event_status in event_statuses:
        tips += event_status.tip_amount
    return tips/float(revenue)


def get_event_attendees(events):
    app_attendees = EventStatus.objects.filter(event__in=events, refund_authorization__isnull=True)
    web_payments = CashPayment.objects.filter(event__in=events)
    web_attendees = 0
    for payment in web_payments:
        web_attendees = web_attendees + payment.attendees
    total_attendees = len(app_attendees) + web_attendees
    redeemed_attendees = app_attendees.filter(status="R").count() + web_attendees
    return redeemed_attendees, total_attendees


def get_event_stats(min_date=datetime.now()-timedelta(weeks=4), max_date=datetime.now(), market=None):
    if market:
        lat = market_dict[market]['lat']
        lng = market_dict[market]['lng']
        venues = get_venues_within_distance_for_events(lat, lng, large_radius)
        sponsored_events = SponsoredEvent.objects.filter(place__in=venues, start__gte=min_date, start__lte=max_date, active=True)
    else:
        sponsored_events = SponsoredEvent.objects.filter(start__gte=min_date, start__lte=max_date, active=True)
    redeemed_attendees, total_attendees = get_event_attendees(sponsored_events)
    revenue, redeemed_revenue, unredeemed_revenue, cash_revenue = get_revenue_for_events(sponsored_events)
    # nps_score = get_nps_score(sponsored_events)
    # promoters, passives, detractors = get_nps_breakdown(sponsored_events)
    # total_responses = len(promoters) + len(passives) + len(detractors)
    # MoM_revenue_growth = 0
    average_tip_percentage = get_tip_percentage(sponsored_events, revenue)
    total_event_attendees = 0
    percent_repeat_attendees = 0
    print "Total Attendees: " + str(total_attendees)
    print "Redeemed Attendees: " + str(redeemed_attendees)
    print "Total Revenue: " + str(revenue)
    print "Revenue from App: " + str(redeemed_revenue+unredeemed_revenue)
    print "Revenue from Cash: " + str(cash_revenue)
    # print "NPS: " + str(nps_score)
    # print "Total NPS Responses: " + str(total_responses)
    # print "Promoter %: " + str(len(promoters)/float(total_responses))
    # print "Passive %: " + str(len(passives)/float(total_responses))
    # print "Detractor %: " + str(len(detractors)/float(total_responses))
    print "Tip %: " + str(average_tip_percentage)
    print "Number of Events: " + str(len(sponsored_events))
    print "Revenue/Event: " + str(float(revenue)/len(sponsored_events))


def get_event_attendees_over_time(start_date=datetime.now(), number_of_weeks=10):
    market = "SEA"
    lat = market_dict[market]['lat']
    lng = market_dict[market]['lng']
    venues = get_venues_within_distance_for_events(lat, lng, large_radius)
    sponsored_events = SponsoredEvent.objects.filter(place__in=venues, start__lte=start_date)
    total_attendees = EventStatus.objects.filter(event__in=sponsored_events, status=EVENT_STATUS.REDEEMED).distinct('user')
    print "Attendees To-Date: " + str(len(total_attendees))
    # for week in range(0, number_of_weeks):
    #     today = start_date - timedelta(weeks=week)
    #     last_week = start_date - timedelta(weeks=week + 1)
    #     two_weeks_ago = start_date - timedelta(weeks=week + 2)


def get_old_event_attendees():
    deals = [207, 210, 213]
    deal_statuses = DealStatus.objects.filter(deal_id__in=deals)
    old_users = deal_statuses.values_list('user', flat=True)
    return old_users


def get_repeat_attendees(redeemed_attendee_statuses, sponsored_events):
    repeat_users = []
    friend_of_repeat_user = []
    for status in redeemed_attendee_statuses:
        older_events = sponsored_events.filter(start__lt=status.event.start)
        first_events_users = get_old_event_attendees()
        users_at_old_events = EventStatus.objects.filter(event__in=older_events).exclude(event=status.event).exclude(status=EVENT_STATUS.INTERESTED).exclude(status=EVENT_STATUS.INTERESTED).values_list('user', flat=True)
        all_old_users = list(first_events_users) + list(users_at_old_events)
        if status.user.id in all_old_users:
            repeat_users.append(status.user)

    for user in repeat_users:
        friends = Friendship.objects.filter(user=user).values_list('friend', flat=True)
        # print "Total Friends: " + str(len(friends))
        friends_at_event = redeemed_attendee_statuses.filter(user_id__in=friends).exclude(user__in=repeat_users)
        friend_of_repeat_user.extend(friends_at_event)
    return len(repeat_users), len(set(friend_of_repeat_user))


def get_average_number_of_friends_at_event(redeemed_attendee_statuses, sponsored_events):
    repeat_users = []
    non_repeat_users = []
    for status in redeemed_attendee_statuses:
        older_events = sponsored_events.filter(start__lt=status.event.start)
        if EventStatus.objects.filter(user=status.user, event__in=older_events).exclude(event=status.event).exclude(status=EVENT_STATUS.INTERESTED).exclude(status=EVENT_STATUS.INTERESTED).exists():
            repeat_users.append(status.user)
        else:
            non_repeat_users.append(status.user)
    repeat_total = 0
    for user in repeat_users:
        friends = Friendship.objects.filter(user=user).values_list('friend', flat=True)
        # print "Total Friends: " + str(len(friends))
        friends_at_event = redeemed_attendee_statuses.filter(user_id__in=friends)
        repeat_total += len(friends_at_event)
    non_repeat_total = 0
    for user in non_repeat_users:
        friends = Friendship.objects.filter(user=user).values_list('friend', flat=True)
        # print "Total Friends: " + str(len(friends))
        friends_at_event = redeemed_attendee_statuses.filter(user_id__in=friends)
        non_repeat_total += len(friends_at_event)
    if len(repeat_users) != 0:
        return repeat_total/float(len(repeat_users)), non_repeat_total/float(len(non_repeat_users))
    else:
        return 0, 0


def get_friends_at_event(event_statuses_of_earlier):
    friends_list = []
    for event_status in event_statuses_of_earlier:
        friends = Friendship.objects.filter(user=event_status.user).values_list('friend', flat=True)
        event = event_status.event
        friends_at_event = EventStatus.objects.filter(event=event, status=EVENT_STATUS.REDEEMED, user_id__in=friends).exclude(pk__in=[x.id for x in event_statuses_of_earlier])
        friends_list.extend(friends_at_event)
    return set(friends_list)


def get_event_stats_in_time_period(min_date=datetime.now()-timedelta(weeks=4), max_date=datetime.now()):
    venues = get_venues_within_distance(47.66759, -122.312766, 20)
    all_sponsored_events = SponsoredEvent.objects.filter(place__in=venues)
    sponsored_events = SponsoredEvent.objects.filter(place__in=venues, start__lte=max_date, start__gte=min_date)
    redeemed_attendee_statuses = EventStatus.objects.filter(event__in=sponsored_events).filter(Q(status=EVENT_STATUS.REDEEMED) | Q(status=EVENT_STATUS.GOING))
    older_events = all_sponsored_events.filter(start__lt=min_date)
    first_events_users = get_old_event_attendees()
    users_at_old_events = EventStatus.objects.filter(event__in=older_events, status=EVENT_STATUS.REDEEMED).values_list('user', flat=True)
    all_old_users = list(first_events_users) + list(users_at_old_events)
    repeat_revenue = 0
    print "Total Attendees: " + str(len(set(all_old_users)))
    for status in redeemed_attendee_statuses:
        if status.user.id in all_old_users:
            repeat_revenue += status.event.item_price
    print "Revenue from Repeat: " + str(repeat_revenue)
    print "Repeat Revenue/User: " + str(float(repeat_revenue)/len(set(all_old_users)))


def print_event_numbers():
    user = User.objects.get(username="6094398069")
    facebook_api = facebook.GraphAPI(access_token=user.profile.fb_token)
    sponsored_events = SponsoredEvent.objects.filter(active=True, start__lte=datetime.now()).order_by('start')
    for event in sponsored_events:
        venue_name = event.place.name
        # try:
        # going = facebook_api.get_object(id=event.facebook_event_id + "/attending")
        # interested = facebook_api.get_object(id=event.facebook_event_id + "/interested")
        # going_count = len(going['data'])
        # interested_count = len(interested['data'])
        redeemed_attendees = EventStatus.objects.filter(event=event).filter(status=EVENT_STATUS.REDEEMED)
        repeat_attendees, friends_of_repeat_attendees = get_repeat_attendees(redeemed_attendees, sponsored_events)
        unredeemed_attendees = EventStatus.objects.filter(event=event).filter(status=EVENT_STATUS.GOING)
        attendees_before = EventStatus.objects.filter(event=event, date_created__lte=event.start - timedelta(days=1)).filter(Q(status=EVENT_STATUS.REDEEMED) | Q(status=EVENT_STATUS.GOING))
        other_friends_at_event = get_friends_at_event(attendees_before)
        price_point = event.item_price
        average_number_of_friends_for_repeat, average_number_of_friends_for_non_repeat = get_average_number_of_friends_at_event(redeemed_attendees, sponsored_events)
        print str(venue_name)
        print str(price_point)
        # print str(going_count)
        # print str(interested_count)
        print str(len(redeemed_attendees))
        print str(len(unredeemed_attendees))
        print "Before: " + str(len(attendees_before))
        print "At Event: " + str(len(other_friends_at_event))
        print str(repeat_attendees)
        print str(friends_of_repeat_attendees)
        print str(average_number_of_friends_for_repeat)
        print str(average_number_of_friends_for_non_repeat)
        print ""


def upcoming_event_numbers():
    user = User.objects.get(username="5413359388")
    facebook_api = facebook.GraphAPI(access_token=user.profile.fb_token)
    sponsored_event = SponsoredEvent.objects.filter(active=True, start__gte=datetime.now())
    for event in sponsored_event:
        attendees = facebook_api.get_object(id=event.facebook_event_id + "/attending")
        interested = facebook_api.get_object(id=event.facebook_event_id + "/interested")
        attendee_count = get_event_count(attendees)
        interested_count = get_event_count(interested)
        e = EventStatus.objects.filter(event=event, status="U")
        x = EventStatus.objects.filter(event=event, status="R")
        print "Venue: " + event.place.name
        print "Going: " + str(attendee_count)
        print "Interested: " + str(interested_count)
        print "Reservations " + str(len(e) + len(x))
        print ""
        # data = get_ad_data(event)


def upcoming_events(event_ids):
    user = User.objects.get(username="5413359388")
    facebook_api = facebook.GraphAPI(access_token=user.profile.fb_token)
    for event_id in event_ids:
        event_info = facebook_api.get_object(id=event_id)
        attendees = facebook_api.get_object(id=event_id + "/attending")
        interested = facebook_api.get_object(id=event_id + "/interested")
        attendee_count = get_event_count(attendees)
        interested_count = get_event_count(interested)
        print "Place: " + event_info['venue']['city']
        # print "Description: " + event_info['description']
        print "Going: " + str(attendee_count)
        print "Interested: " + str(interested_count)
        print "Days Remaining: "
        print ""


# def get_ad_data(event):
#     user = User.objects.get(username="5413359388")
#     access_token = "EAAKijrdivowBABFhM27DVfgH0GneI7EoS1ssKMTQRUxd7wDtH50CW5TlNlXZBQUXTJj9trJa8mcWsbOPypMVifUClhdo6FYbH8aO7ZATS35A9sidjAYUtTZAqeEayg3QcylDwL0r8UGyG9QuWuhWoKJQt0OGY71RYoLmNbgFwZDZD"
#     ads_api = FacebookAdsApi.init(settings.FACEBOOK_APP_ID, settings.FACEBOOK_APP_SECRET, access_token)


def get_event_count(response):
    return len(response['data'])


def dashboard_query(facebook_ids):
    going_count = []
    interested_count = []
    reservation_count = []
    user = User.objects.get(username="5413359388")
    facebook_api = facebook.GraphAPI(access_token=user.profile.fb_token)
    for event_id in facebook_ids:
        attendees = facebook_api.get_object(id=event_id + "/attending")
        interested = facebook_api.get_object(id=event_id + "/interested")
        going_count.append(get_event_count(attendees))
        interested_count.append(get_event_count(interested))
        if SponsoredEvent.objects.filter(facebook_event_id=event_id).exists():
            event = SponsoredEvent.objects.get(facebook_event_id=event_id)
            e = EventStatus.objects.filter(event=event, status="U", refund_authorization__isnull=True)
            x = EventStatus.objects.filter(event=event, status="R", refund_authorization__isnull=True)
            c = CashPayment.objects.filter(event=event)
            attendees = 0
            for payment in c:
                attendees = payment.attendees + attendees
            reservation_count.append(str(len(e) + len(x) + attendees))
        else:
            reservation_count.append("None")
    for facebook_id in facebook_ids:
        print facebook_id
    print ""
    for going in going_count:
        print going
    print ""
    for interested in interested_count:
        print interested
    print ""
    for reservation in reservation_count:
        print reservation
    print ""



def simplified_dashboard_query(facebook_ids):
    going_count = []
    interested_count = []
    reservation_count = []
    user = User.objects.get(username="5413359388")
    for event_id in facebook_ids:
        # going_count.append(get_event_count(attendees))
        # interested_count.append(get_event_count(interested))
        if SponsoredEvent.objects.filter(facebook_event_id=event_id).exists():
            event = SponsoredEvent.objects.get(facebook_event_id=event_id)
            e = EventStatus.objects.filter(event=event, status="U", refund_authorization__isnull=True)
            x = EventStatus.objects.filter(event=event, status="R", refund_authorization__isnull=True)
            c = CashPayment.objects.filter(event=event)
            attendees = 0
            for payment in c:
                attendees = payment.attendees + attendees
            reservation_count.append(str(len(e) + len(x) + attendees))
        else:
            reservation_count.append("None")
    for facebook_id in facebook_ids:
        print facebook_id
    print ""
    # for going in going_count:
    #     print going
    # print ""
    # for interested in interested_count:
    #     print interested
    print ""
    for reservation in reservation_count:
        print reservation
    print ""


def get_dating_profiles_for_event(sponsored_event):
    user_ids_at_event = EventStatus.objects.filter(event=sponsored_event).filter(Q(status=EVENT_STATUS.REDEEMED) | Q(status=EVENT_STATUS.GOING)).values_list('user', flat=True)
    profiles = Profile.objects.filter(user_id__in=user_ids_at_event)
    dating_profiles = DatingProfile.objects.filter(dating_profile__in=profiles)
    return dating_profiles


def swipe_and_match_stats(min_date=datetime.now()-timedelta(weeks=4), max_date=datetime.now()):
    events = SponsoredEvent.objects.filter(start__gte=min_date, start__lte=max_date)
    total_dating_profiles = []
    total_iphone_users = []
    for sponsored_event in events:
        # android_ids = AndroidDevice.objects.all().values_list('user', flat=True)
        user_ids_at_event = EventStatus.objects.filter(event=sponsored_event, status="R").values_list('user', flat=True)
        # users = User.objects.filter(pk__in=user_ids_at_event).exclude(pk__in=android_ids)
        users = User.objects.filter(pk__in=user_ids_at_event)
        profiles = Profile.objects.filter(user__in=users)
        dating_profiles = DatingProfile.objects.filter(dating_profile__in=profiles)
        males_searching_for_females = dating_profiles.filter(user_gender="M", preference="F")
        females_searching_for_males = dating_profiles.filter(user_gender="F", preference="M")
        total_dating_profiles.extend(dating_profiles)
        total_iphone_users.extend(users)
        total_possible_swipes = get_total_possible_swipes(dating_profiles, sponsored_event.id)
        total_swipes = DatingMatch.objects.filter(dating_profile_selector__in=dating_profiles, event=sponsored_event).count()
        right_swipes = DatingMatch.objects.filter(dating_profile_selector__in=dating_profiles, event=sponsored_event, is_selected=True).count()
        match_swipes = get_match_swipe_count(dating_profiles, sponsored_event.id)
        if len(dating_profiles) > 0:
            print sponsored_event.place.name
            print "Men => Women: " + str(len(males_searching_for_females))
            print "Women => Men: " + str(len(females_searching_for_males))
            if total_possible_swipes > 0:
                print "Swipe Completion Percentage: " + str(total_swipes/float(total_possible_swipes))
            if total_swipes > 0:
                print "Percentage Swipe Right: " + str(right_swipes/float(total_swipes))
                print "Total Matches: " + str(match_swipes)
                print "Match Percentage: " + str(match_swipes/float(total_swipes))
            print str(len(users))
            print len(dating_profiles)/float(len(users))
            print ""
    print "Overall Profiles Created: " + str(len(total_dating_profiles) / float(len(total_iphone_users)))


def get_total_possible_swipes(dating_profiles, event_id):
    swipe_count = 0
    for dating_profile in dating_profiles:
        dating_queue = get_full_dating_queue(dating_profile.dating_profile.user, event_id)
        swipe_count += len(dating_queue)
    return swipe_count


def get_full_dating_queue(user, event_id, dating_profile=None):
    user_dating_profile = DatingProfile.objects.get(dating_profile=user.profile)
    # already_swiped_profile_ids_to_exclude = DatingMatch.objects.filter(event_id=event_id, dating_profile_selector=user_dating_profile).values_list('dating_profile_selectee', flat=True)
    # profile_ids_to_exclude = DatingProfile.objects.filter(pk__in=already_swiped_profile_ids_to_exclude).values_list('dating_profile', flat=True)
    event = SponsoredEvent.objects.get(pk=event_id)
    event_attendees = EventStatus.objects.filter(event=event).exclude(status=EVENT_STATUS.INTERESTED).exclude(status=EVENT_STATUS.NO_SELECTION).values_list('user_id', flat=True)
    profile_ids = Profile.objects.filter(user_id__in=event_attendees).exclude(user_id=user.id).values_list('pk', flat=True)
    dating_profiles = DatingProfile.objects.filter(dating_profile_id__in=profile_ids, user_gender=user_dating_profile.preference, preference=user_dating_profile.user_gender)
    return dating_profiles


def get_match_swipe_count(dating_profiles, event_id):
    count = 0
    for dating_profile in dating_profiles:
        matches = DatingMatch.objects.filter(dating_profile_selector=dating_profile, event_id=event_id, is_selected=True)
        for match in matches:
            selectee = match.dating_profile_selectee
            if DatingMatch.objects.filter(dating_profile_selector=selectee, event_id=event_id, dating_profile_selectee=dating_profile, is_selected=True).exists():
                count += 1
    return count


def event_predictor(min_date=datetime.now()-timedelta(weeks=4), max_date=datetime.now()):
    sponsored_events = SponsoredEvent.objects.filter(start__gte=min_date, start__lte=max_date)
    for event in sponsored_events:
        total_attendees = EventStatus.objects.filter(event=event, status="R").count()
        total_purchases = EventStatus.objects.filter(event=event).filter(Q(status="R") | Q(status="U"))
        five_days_out = total_purchases.filter(date_created__lte=event.start-timedelta(days=5)).count()
        four_days_out = total_purchases.filter(date_created__lte=event.start - timedelta(days=4)).count()
        three_days_out = total_purchases.filter(date_created__lte=event.start - timedelta(days=3)).count()
        two_days_out = total_purchases.filter(date_created__lte=event.start - timedelta(days=2)).count()
        one_day_out = total_purchases.filter(date_created__lte=event.start - timedelta(days=1)).count()
        print str(event.place.name)
        print str(total_attendees)
        print "Five Days Out: " + str(five_days_out/float(total_attendees))
        print "Four Days Out: " + str(four_days_out / float(total_attendees))
        print "Three Days Out: " + str(three_days_out / float(total_attendees))
        print "Two Days Out: " + str(two_days_out / float(total_attendees))
        print "One Days Out: " + str(one_day_out / float(total_attendees))
        print ""


def get_facebook_ids(event_id):
    user = User.objects.get(username="5413359388")
    facebook_api = facebook.GraphAPI(access_token=user.profile.fb_token)
    going = facebook_api.get_object(id=event_id + "/attending")
    interested = facebook_api.get_object(id=event_id + "/interested")
    going_ids = get_facebook_ids_from_events(going)
    interested_ids = get_facebook_ids_from_events(interested)
    return going_ids, interested_ids


def get_facebook_ids_from_events(going):
    facebook_ids = []
    paging = True
    facebook_ids = add_fb_ids(facebook_ids, going['data'])
    while paging:
        if 'paging' in going:
            if 'next' in going['paging']:
                url = going['paging']['next']
                response = requests.get(url)
                going = json.loads(response.text)
                facebook_ids = add_fb_ids(facebook_ids, going['data'])
            else:
                paging = False
        else:
            paging = False
    return facebook_ids


def add_fb_ids(facebook_ids, going):
    for going_obj in going:
        facebook_ids.append(going_obj['id'])
    return facebook_ids


def get_unsubscribes(min_date = datetime.now()-timedelta(days=1), max_date=datetime.now()):
    unsubscribes = EmailResponse.objects.filter(status="UN", date_created__gte=min_date, date_created__lte=max_date)
    print "Unsubscribes: " + str(len(unsubscribes))


def email_stats(min_date = datetime.now()-timedelta(weeks=2), max_date = datetime.now() + timedelta(weeks=2)):
    events = SponsoredEvent.objects.filter(start__gte=min_date, start__lte=max_date)
    for event in events:
        if EmailCampaignTracker.objects.filter(event=event).exists():
            print event.place.name
            campaigns = EmailCampaignTracker.objects.filter(event=event)
            for campaign in campaigns:
                category = campaign.category
                print campaign.subject
                email_delivered = EmailStatus.objects.filter(category=category, event="delivered")
                email_unique_opens = EmailStatus.objects.filter(category=category, event="open").distinct('email')
                email_total_opens = EmailStatus.objects.filter(category=category, event="open")
                email_clicks = EmailStatus.objects.filter(category=category, event="click")
                print "Delivered: " + str(len(email_delivered))
                print "Unique Opens: " + str(len(email_unique_opens)) + " - " + str(len(email_unique_opens)/float(len(email_delivered)))
                print "Total Opens: " + str(len(email_total_opens))+ " - " + str(len(email_total_opens)/float(len(email_delivered)))
                print "Clicks: " + str(len(email_clicks))+ " - " + str(len(email_clicks)/float(len(email_delivered)))
            print ""


def get_submitted_emails(market, min_date, max_date):
    emails = Emails.objects.filter(market=market, date_created__gte=min_date, date_created__lte=max_date).values_list('email', flat=True)
    return emails


def get_submitted_emails_for_event(event, min_date, max_date):
    market = event.market
    emails_from_event = Emails.objects.filter(event=event).values_list('email', flat=True)
    emails_from_market = Emails.objects.filter(market=market, event__isnull=True, date_created__gte=min_date, date_created__lte=max_date).values_list('email', flat=True)
    all_emails = list(emails_from_event) + list(emails_from_market)
    return set(all_emails)


default_range = .3


def get_user_emails(market, min_date, max_date):
    users = get_user_within_range(market.latitude, market.longitude, default_range)
    emails = users.filter(date_joined__gte=min_date, date_joined__lte=max_date).values_list('email', flat=True)
    return emails


def get_cash_payment_emails(market, min_date, max_date):
    places = get_venues_within_distance_for_events(market.latitude, market.longitude, 40)
    events = SponsoredEvent.objects.filter(place__in=places)
    emails = CashPayment.objects.filter(event__in=events, email__isnull=False, date_created__gte=min_date, date_created__lte=max_date).values_list('email', flat=True)
    return emails


def get_users(market, min_date, max_date):
    users = get_user_within_range(market.latitude, market.longitude, default_range)
    users_in_date_range = users.filter(date_joined__gte=min_date, date_joined__lte=max_date).exclude(pk__in=excluded_users)
    return users_in_date_range


def get_users_who_attended_event(market, min_date, max_date):
    users = get_user_within_range(market.latitude, market.longitude, default_range)
    users_in_date_range = users.filter(date_joined__gte=min_date, date_joined__lte=max_date).exclude(pk__in=excluded_users)
    events = SponsoredEvent.objects.filter(start__lte=max_date)
    user_ids = EventStatus.objects.filter(status="R", user__in=users_in_date_range, event__in=events).values_list('user', flat=True)
    users_who_attended_events = User.objects.filter(pk__in=user_ids)
    return users_who_attended_events


def get_emails_for_market(market, min_date, max_date):
    user_emails = get_user_emails(market, min_date, max_date)
    cash_payment_emails = get_cash_payment_emails(market, min_date, max_date)
    submitted_emails = get_submitted_emails(market, min_date, max_date)
    all_emails = list(user_emails) + list(cash_payment_emails) + list(submitted_emails)
    filtered_emails = []
    for email in all_emails:
        filtered_emails.append(email.lower())
    return set(filtered_emails)


def get_emails_for_event(event, min_date, max_date):
    market = event.market
    user_emails = get_user_emails(market, min_date, max_date)
    cash_payment_emails = get_cash_payment_emails(market, min_date, max_date)
    submitted_emails = get_submitted_emails_for_event(event, min_date, max_date)
    all_emails = list(user_emails) + list(cash_payment_emails) + list(submitted_emails)
    filtered_emails = []
    for email in all_emails:
        filtered_emails.append(email.lower())
    return set(filtered_emails)


# def get_submitted_emails_for_event(event):
#     emails = Emails.objects.filter(event=event).values_list(
#         'email', flat=True)
#     return emails


def get_event_ids_in_market(market):
    lat = market.latitude
    lng = market.longitude
    lat_range = [lat-0.3, lat+0.3]
    lng_range = [lng-0.3, lng+0.3]
    deal_places = DealPlace.objects.filter(latitude__range=lat_range, longitude__range=lng_range)
    event_ids = SponsoredEvent.objects.filter(place__in=deal_places).values_list('pk', flat=True)
    return event_ids


def get_arpu_estimate():
    min_date = datetime(2016, 1, 1)
    max_date = datetime.now() - timedelta(days=153)
    # markets = [13, 20, 9, 10]
    markets = [13]
    markets = Market.objects.filter(pk__in=markets)
    total_users_over_three_months = 0
    total_revenue_over_three_months = 0
    for market in markets:
        # emails = get_emails_for_market(market, min_date, max_date)
        # number_of_emails = len(emails)
        users_in_range = get_users(market, min_date, max_date)
        events_in_market = get_event_ids_in_market(market)
        events = SponsoredEvent.objects.filter(pk__in=events_in_market, start__gte=max_date, start__lte=datetime.now())
        event_statuses = EventStatus.objects.filter(event__in=events, user__in=users_in_range).exclude(status="I").exclude(status="N").exclude(status="F")
        total_revenue = get_revenue_from_event_statuses(event_statuses)
        unique_events = event_statuses.distinct('event').values_list('event', flat=True)
        unique_users = event_statuses.distinct('event').values_list('user', flat=True)
        print market.name
        print "Total Events: " + str(len(unique_events))
        print "Total Users: " + str(len(users_in_range))
        print "Total Revenue: " + str(total_revenue)
        print str(total_revenue/float(len(users_in_range)))
        total_users_over_three_months = total_users_over_three_months + len(users_in_range)
        total_revenue_over_three_months = total_revenue_over_three_months + total_revenue
        print ""
    print "Total: "  + str(total_revenue_over_three_months/float(total_users_over_three_months))


def get_arpu_for_attendees():
    min_date = datetime(2016, 1, 1)
    max_date = datetime.now() - timedelta(days=91)
    markets = [13, 20, 9, 10]
    markets = Market.objects.filter(pk__in=markets)
    total_users_over_three_months = 0
    total_revenue_over_three_months = 0
    for market in markets:
        # emails = get_emails_for_market(market, min_date, max_date)
        # number_of_emails = len(emails)
        users_in_range = get_users_who_attended_event(market, min_date, max_date)
        events_in_market = get_event_ids_in_market(market)
        events = SponsoredEvent.objects.filter(pk__in=events_in_market, start__gte=max_date, start__lte=datetime.now())
        event_statuses = EventStatus.objects.filter(event__in=events, user__in=users_in_range).exclude(status="I").exclude(status="N").exclude(status="F")
        total_revenue = get_revenue_from_event_statuses(event_statuses)
        print market.name
        print "Total Events: " + str(len(events))
        print "Total Users: " + str(len(users_in_range))
        print "Total Revenue: " + str(total_revenue)
        print str(total_revenue/float(len(users_in_range)))
        total_users_over_three_months = total_users_over_three_months + len(users_in_range)
        total_revenue_over_three_months = total_revenue_over_three_months + total_revenue
        print ""
    print "Total: " + str(total_revenue_over_three_months/float(total_users_over_three_months))


def get_user_revenue_stats(market_ids=[7, 9, 10, 11, 13, 16, 17, 18, 19, 21, 22, 23, 20]):
    # market_ids= [1]
    # market_ids = [7, 9, 10, 11, 13, 16, 17, 18, 19, 21, 22, 23, 20]
    # market_ids = [9, 10, 13, 16, 17, 18, 19, 21, 23, 20]
    # market_ids = [1, 13, 20, 10]
    markets = Market.objects.filter(pk__in=market_ids)
    for i in range(0, 8):
        print str(i) + " months ago"
        all_users = []
        for market in markets:
            users_in_range = get_users(market, datetime.now()-timedelta(weeks=4 * (i + 1)), datetime.now()-timedelta(weeks=(4 * i)))
            all_users.extend(users_in_range)
        unique_users = set(all_users)
        total_tickets_sold = EventStatus.objects.filter(user__in=unique_users).exclude(status="I").exclude(status="N").exclude(status="F")
        revenue = get_revenue_from_event_statuses(total_tickets_sold)
        one_time_users = []
        retained_users = []
        for user in unique_users:
            if EventStatus.objects.filter(user=user).exclude(status="I").exclude(status="N").exclude(status="F").count() > 1:
                retained_users.append(user)
            elif EventStatus.objects.filter(user=user).exclude(status="I").exclude(status="N").exclude(status="F").count() == 1:
                one_time_users.append(user)
        tickets_sold_to_retained_user = EventStatus.objects.filter(user__in=retained_users).exclude(status="I").exclude(status="N").exclude(status="F")
        average_revenue_per_ticket = revenue/float(len(total_tickets_sold))
        average_tickets_sold_to_retained_user = len(tickets_sold_to_retained_user)/float(len(retained_users))
        # average_revenue_per_user = ((len(one_time_users) * average_revenue_per_ticket) + (len(retained_users) * average_tickets_sold_to_retained_user * average_revenue_per_ticket))/float(len(unique_users))
        average_revenue_per_user = revenue/(float(len(one_time_users) + len(retained_users)))
        print "Average rev/Ticket: " + str(average_revenue_per_ticket)
        print "Users in this cohort: " + str(len(unique_users))
        print "One time users in this cohort: " + str(len(one_time_users))
        print "Retained users in this cohort: " + str(len(retained_users))
        print "retained/total redeemers: " + str(len(retained_users)/float(len(one_time_users)+len(retained_users)))
        print "% redeemeed: " + str((len(one_time_users)+len(retained_users))/float(len(unique_users)))
        print "% of users who bought one ticket: " + str(len(one_time_users)/float(len(unique_users)))
        print "% of users who bought more than one ticket: " + str(len(retained_users)/float(len(unique_users)))
        print "average tickets sold to retained user: " + str((len(tickets_sold_to_retained_user)) / float(len(retained_users)))
        print "average revenue per user: " + str(average_revenue_per_user)
        print ""


def get_user_revenue_stats_for_user_set(users):
    # market_ids= [1]
    # market_ids = [7, 9, 10, 11, 13, 16, 17, 18, 19, 21, 22, 23, 20]
    # market_ids = [9, 10, 13, 16, 17, 18, 19, 21, 23, 20]
    # market_ids = [9, 13, 20, 10]
    for i in range(0, 8):
        print str(i) + " months ago"
        users_in_range = users.filter(date_joined__gte=datetime.now()-timedelta(weeks=4 * (i + 1)), date_joined__lte=datetime.now()-timedelta(weeks=(4 * i))).exclude(pk__in=excluded_users)
        unique_users = set(users_in_range)
        total_tickets_sold = EventStatus.objects.filter(user__in=unique_users).exclude(status="I").exclude(status="N").exclude(status="F")
        revenue = get_revenue_from_event_statuses(total_tickets_sold)
        one_time_users = []
        retained_users = []
        for user in unique_users:
            if EventStatus.objects.filter(user=user).exclude(status="I").exclude(status="N").exclude(status="F").count() > 1:
                retained_users.append(user)
            elif EventStatus.objects.filter(user=user).exclude(status="I").exclude(status="N").exclude(status="F").count() == 1:
                one_time_users.append(user)
        tickets_sold_to_retained_user = EventStatus.objects.filter(user__in=retained_users).exclude(status="I").exclude(status="N").exclude(status="F")
        average_revenue_per_ticket = revenue/float(len(total_tickets_sold))
        average_tickets_sold_to_retained_user = len(tickets_sold_to_retained_user)/float(len(retained_users))
        # average_revenue_per_user = ((len(one_time_users) * average_revenue_per_ticket) + (len(retained_users) * average_tickets_sold_to_retained_user * average_revenue_per_ticket))/float(len(unique_users))
        average_revenue_per_user = revenue/float(len(unique_users))
        print "Average rev/Ticket: " + str(average_revenue_per_ticket)
        print "Users in this cohort: " + str(len(unique_users))
        print "One time users in this cohort: " + str(len(one_time_users))
        print "Retained users in this cohort: " + str(len(retained_users))
        print "retained/total redeemers: " + str(len(retained_users)/float(len(one_time_users)+len(retained_users)))
        print "% redeemeed: " + str((len(one_time_users)+len(retained_users))/float(len(unique_users)))
        print "% of users who bought one ticket: " + str(len(one_time_users)/float(len(unique_users)))
        print "% of users who bought more than one ticket: " + str(len(retained_users)/float(len(unique_users)))
        print "average tickets sold to retained user: " + str((len(tickets_sold_to_retained_user)) / float(len(retained_users)))
        print "average revenue per user: " + str(average_revenue_per_user)
        print ""


def get_this_weeks_event_managers():
    events = SponsoredEvent.objects.filter(start__gte=datetime.now(), start__lte=datetime.now()+timedelta(weeks=1))
    for event in events:
        print event.place.name
        event_staffers = EventStaffer.objects.filter(status="PR", event=event)
        for staffer in event_staffers:
            print staffer.manager.name + " " + staffer.manager.phone_number
        print ""


def get_previous_event_in_market(current_event):
    market = current_event.market
    events = SponsoredEvent.objects.filter(market=market, start__lt=current_event.start).order_by('-start')
    if events:
        return events[0]
    else:
        return None


# def get_email_stats_for_single_event(facebook_event_id):
#     current_event = SponsoredEvent.objects.get(facebook_event_id=facebook_event_id)
#     total_emails = 0
#     print current_event.place.name
#     previous_event = get_previous_event_in_market(current_event)
#     if previous_event:
#         min_date = previous_event.end + timedelta(days=1)
#         max_date = current_event.end + timedelta(days=1)
#         emails = get_emails_for_event(current_event, min_date, max_date)
#         print "Emails for this Event: " + str(len(emails))
#     else:
#         min_date = current_event.date_created
#         max_date = current_event.end + timedelta(days=1)
#         emails = get_emails_for_event(current_event, min_date, max_date)
#         print "Emails for this Event (FIRST): " + str(len(emails))
#     total_spent = HotspotFacebookAds().spent_on_event(current_event)
#     if total_spent:
#         if len(emails)>0:
#             cost_per_email = total_spent/float(len(emails))
#             print "Total Spent: " + str(total_spent)
#             print "Cost per Email: " + str(cost_per_email)
#     total_emails = total_emails + len(emails)


# def get_email_stats_for_event(min_date=datetime.now(), max_date=datetime.now() + timedelta(weeks=8)):
#     events = SponsoredEvent.objects.filter(end__lte=max_date, end__gte=min_date)
#     total_emails = 0
#     for current_event in events:
#         print current_event.place.name
#         previous_event = get_previous_event_in_market(current_event)
#         if previous_event:
#             min_date = previous_event.end + timedelta(days=1)
#             max_date = current_event.end + timedelta(days=1)
#             emails = get_emails_for_event(current_event, min_date, max_date)
#             print "Emails for this Event: " + str(len(emails))
#         else:
#             min_date = current_event.date_created
#             max_date = current_event.end + timedelta(days=1)
#             emails = get_emails_for_event(current_event, min_date, max_date)
#             print "Emails for this Event (FIRST): " + str(len(emails))
#         total_spent = HotspotFacebookAds().spent_on_event(current_event)
#         if total_spent:
#             if len(emails)>0:
#                 cost_per_email = total_spent/float(len(emails))
#                 print "Total Spent: " + str(total_spent)
#                 print "Cost per Email: " + str(cost_per_email)
#         total_emails = total_emails + len(emails)
#         print ""
#     average_emails = str(total_emails/float(len(events)))
#     print "AVERAGE EMAILS: " + average_emails


# def get_email_stats_for_event(min_date=datetime.now(), max_date=datetime.now() + timedelta(weeks=4)):
#     events = SponsoredEvent.objects.filter(end__lte=max_date, end__gte=min_date)
#     total_emails = 0
#     for current_event in events:
#         print current_event.place.name
#         previous_event = get_previous_event_in_market(current_event)
#         if previous_event:
#             min_date = previous_event.end + timedelta(days=1)
#             max_date = current_event.end + timedelta(days=1)
#             emails = get_emails_for_event(current_event, current_event.market, min_date, max_date)
#             print "Emails for this Event: " + str(len(emails))
#         else:
#             max_date = current_event.end + timedelta(days=1)
#             emails = get_emails_for_event(current_event, current_event.market, max_date - timedelta(weeks=8), max_date)
#             print "Emails for this Event (FIRST): " + str(len(emails))
#         total_spent = HotspotFacebookAds().spent_on_event(current_event)
#         if total_spent:
#             if len(emails)>0:
#                 cost_per_email = total_spent/float(len(emails))
#                 print "Total Spent: " + str(total_spent)
#                 print "Cost per Email: " + str(cost_per_email)
#         total_emails = total_emails + len(emails)
#         print ""
#     average_emails = str(total_emails/float(len(events)))
#     print "AVERAGE EMAILS: " + average_emails


def get_early_access_url(facebook_event_id):
    event = SponsoredEvent.objects.get(facebook_event_id=facebook_event_id)
    url = "http://www.gethotspotapp.com/early-access/" + str(simple_int_hash(event.id))
    return url


def get_early_access_subscription_url(facebook_event_id):
    event = SponsoredEvent.objects.get(facebook_event_id=facebook_event_id)
    url = "http://www.gethotspotapp.com/subscription/" + str(simple_int_hash(event.id))
    return url


def print_events_with_no_facebook_campaign():
    events = SponsoredEvent.objects.filter(facebook_campaign_id__isnull=True).order_by('-start')
    count = 0
    for event in events:
        print event.place.name + " " + str(count)
        print str(event.start) + " " + event.market.name
        print str(event.facebook_event_id)
        count = count + 1
        print ""
    return events


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
        user_obj = User.objects.filter(pk__in=users_in_location, date_joined__gte=datetime(2016, 1, 1))
        user_emails = user_obj.values_list('email', flat=True)
        emails_from_cash = CashPayment.objects.filter(event__in=events_in_market).values_list('email', flat=True)
        market_emails = list(user_emails) + list(emails_from_cash)
        all_emails.extend(market_emails)
    submitted_emails = Emails.objects.all().values_list('email', flat=True)
    all_emails.extend(submitted_emails)
    for email in all_emails:
        if email:
            print email
    return all_emails


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
        user_obj = User.objects.filter(pk__in=users_in_location, date_joined__gte=datetime(2016, 1, 1))
        user_phone_numbers = user_obj.values_list('username', flat=True)
        all_numbers.extend(user_phone_numbers)
    for phone_number in all_numbers:
        if phone_number:
            print phone_number
    return all_numbers


def get_average_friends_per_market(market):
    lat = market.latitude
    lng = market.longitude
    activated_users = EventStatus.objects.filter(status="R").values_list('user', flat=True)
    users = get_user_within_distance(lat, lng, distance=20, max_date=datetime.now(), min_date=datetime(2016, 1, 1))
    users = users.filter(pk__in=activated_users)
    total_friends = 0
    for user in users:
        friend_count = Friendship.objects.filter(user=user, is_blocked=False).filter(user_id__in=activated_users).count()
        total_friends = total_friends + friend_count
    print str(total_friends/float(len(users)))


def split_user_groups_into_push_and_not_push(users):
    # android_ids = AndroidDevice.objects.all().values_list('user', flat=True)
    # users = users.exclude(pk__in=android_ids)
    has_device = ~(Q(ios_devices=None) & Q(android_devices=None))
    with_push = users.filter(has_device).values_list('pk', flat=True)
    without_push = users.exclude(has_device).values_list('pk', flat=True)
    return with_push, without_push


def social_analytics(users=User.objects.all(),min_date = datetime.now() - timedelta(weeks=10) ,max_date = datetime.now()):
    with_push_user_ids, without_push_user_ids = split_user_groups_into_push_and_not_push(users)
    notifications = NotificationTracker.objects.filter(notification_type="ER", date_created__gte=min_date, date_created__lte=max_date)
    notifications_with_push = notifications.filter(recipient_id__in=with_push_user_ids)
    notifications_without_push = notifications.filter(recipient_id__in=without_push_user_ids)
    users_who_purchased_without_push = []
    for x in notifications_without_push:
        date_created = x.date_created
        user = x.recipient
        event_status_unredeemed_ids = EventStatus.objects.filter(status="U", date_created__gte=date_created,
                                                                 date_created__lte=date_created + timedelta(days=1),
                                                                 user=user).values_list('pk', flat=True)
        event_status_redeemed_ids = EventStatus.objects.filter(status="R", date_created__gte=date_created,
                                                               date_created__lte=date_created + timedelta(days=1),
                                                               user=user).values_list('pk', flat=True)
        all_event_status_ids = list(event_status_unredeemed_ids) + list(event_status_redeemed_ids)
        if len(all_event_status_ids) > 0:
            users_who_purchased_without_push.extend(all_event_status_ids)
    users_who_purchased_with_push = []
    for x in notifications_with_push:
        date_created = x.date_created
        user = x.recipient
        event_status_unredeemed_ids = EventStatus.objects.filter(status="U", date_created__gte=date_created,
                                                                 date_created__lte=date_created + timedelta(days=1),
                                                                 user=user).values_list('pk', flat=True)
        event_status_redeemed_ids = EventStatus.objects.filter(status="R", date_created__gte=date_created,
                                                               date_created__lte=date_created + timedelta(days=1),
                                                               user=user).values_list('pk', flat=True)
        all_event_status_ids = list(event_status_unredeemed_ids) + list(event_status_redeemed_ids)
        if len(all_event_status_ids) > 0:
            users_who_purchased_with_push.extend(all_event_status_ids)
    without_push_conv_rate = len(set(users_who_purchased_without_push))/float(len(notifications_without_push))
    with_push_conv_rate = len(set(users_who_purchased_with_push)) / float(len(notifications_with_push))
    print "Without Push Conversion Rate: " + str(without_push_conv_rate)
    print "With Push Conversion Rate: " + str(with_push_conv_rate)
    print "Improvement: " + str((with_push_conv_rate - without_push_conv_rate)/without_push_conv_rate)


def get_attendees_of_event(event):
    event_statuses=EventStatus.objects.filter(event=event, refund_authorization__isnull=True).exclude(status=EVENT_STATUS.INTERESTED).exclude(status=EVENT_STATUS.NO_SELECTION)
    return len(event_statuses)


def print_recurring_revenue_stats():
    recurring_place = []
    one_time_place = []
    place_ids = SponsoredEvent.objects.filter(start__gte=datetime.now()-timedelta(weeks=10)).values_list('place', flat=True)
    for place_id in place_ids:
        if SponsoredEvent.objects.filter(place_id=place_id).count() > 1:
            recurring_place.append(place_id)
        else:
            event = SponsoredEvent.objects.get(place_id=place_id)
            if get_attendees_of_event(event) > 40:
                one_time_place.append(place_id)
    average_recurring_revenue = get_average_revenue_from_places(recurring_place)
    average_one_time_revenue = get_average_revenue_from_places(one_time_place)
    print "Recurring: " + str(average_recurring_revenue)
    print "One-time: " + str(average_one_time_revenue)


def get_average_revenue_from_places(place_ids):
    events = SponsoredEvent.objects.filter(place_id__in=place_ids)
    revenue = 0
    for event in events:
        event_statuses = EventStatus.objects.filter(event=event, refund_authorization__isnull=True).exclude(
            status=EVENT_STATUS.INTERESTED).exclude(status=EVENT_STATUS.NO_SELECTION)
        revenue = revenue + get_revenue_from_event_statuses(event_statuses)
    average_revenue = revenue/len(events)
    return average_revenue


def get_recurring_event_stats(min_date=datetime.now()-timedelta(weeks=4), max_date=datetime.now()):
    sponsored_events = SponsoredEvent.objects.filter(start__gte=min_date, start__lte=max_date, active=True)
    recurring_events = []
    one_time_events = []
    for event in sponsored_events:
        place = event.place
        if SponsoredEvent.objects.filter(place=place, start__lt=event.start).exists():
            recurring_events.append(event)
        else:
            one_time_events.append(event)
    print "Total Events: " + str(len(sponsored_events))
    print "Recurring Events: " + str(len(recurring_events))
    print "One-time Events: " + str(len(one_time_events))


def get_app_installs_and_subscribers(min_date=datetime(2016, 1, 1), max_date=datetime.now()):
    emails = HotspotFacebookAds().get_emails_for_markets(min_date, max_date)
    users = HotspotFacebookAds().get_users_for_markets(min_date, max_date)
    print "Number of emails: " + str(len(emails))
    print "Number of users: " + str(len(users))


def recurring_event_stats():
    places = SponsoredEvent.objects.filter().distinct('place').values_list('place', flat=True)
    recurring_event_places = []
    for place in places:
        if SponsoredEvent.objects.filter(place=place).count() > 1:
            recurring_event_places.append(place)
    for place in recurring_event_places:
        events = SponsoredEvent.objects.filter(place_id=place).order_by('start')
        attended_user_ids = []
        print events[0].place.name
        for event in events:
            nps_score = get_nps_score(event)
            unredeemed, redeemed = get_event_attendees_for_app([event])
            notifications = NotificationTracker.objects.filter(event=event, notification_type=NOTIFICATION_TYPE.EVENT_RESERVED_PUSH)
            print "Date: " + str(event.start)
            print "Event Attendees: " + str(len(unredeemed) + len(redeemed))
            print "NPS Score: " + str(nps_score)
            print "Social notifications sent: " + str(len(notifications))
            redeemed_user_ids = list(redeemed.values_list('user', flat=True))
            unredeemed_user_ids = list(unredeemed.values_list('user', flat=True))
            all_user_ids = redeemed_user_ids + unredeemed_user_ids
            recurring_users = []
            for user_id in all_user_ids:
                if user_id in attended_user_ids:
                    recurring_users.append(user_id)
            friends_of_recurring_users = Friendship.objects.filter(user_id__in=recurring_users).values_list('friend', flat=True)
            event_statuses = EventStatus.objects.filter(event=event, user_id__in=friends_of_recurring_users).exclude(user_id__in=recurring_users).filter(Q(status=EVENT_STATUS.REDEEMED) | Q(status=EVENT_STATUS.GOING))
            print "Recurring users: " + str(len(recurring_users))
            print "All Recurring users + Friends: " + str(len(recurring_users) + len(event_statuses))
            if all_user_ids:
                print "Percentage: " + str(len(recurring_users)/float(len(all_user_ids)))
                print "Percentage with friends: " + str((len(recurring_users) + len(event_statuses))/float(len(all_user_ids)))
            print ""
            attended_user_ids.extend(all_user_ids)
        print ""
        print ""


def recurring_market_stats():
    # places = SponsoredEvent.objects.filter().distinct('place').values_list('place', flat=True)
    # recurring_event_places = []
    # for place in places:
    #     if SponsoredEvent.objects.filter(place=place).count() > 1:
    #         recurring_event_places.append(place)
    markets = Market.objects.all()
    for market in markets:
        events = SponsoredEvent.objects.filter(market=market).order_by('start')
        attended_user_ids = []
        print market.name
        for event in events:
            print event.place.name
            nps_score = get_nps_score(event)
            unredeemed, redeemed = get_event_attendees_for_app([event])
            notifications = NotificationTracker.objects.filter(event=event, notification_type=NOTIFICATION_TYPE.EVENT_RESERVED_PUSH)
            print "Date: " + str(event.start)
            print "Event Attendees: " + str(len(unredeemed) + len(redeemed))
            print "NPS Score: " + str(nps_score)
            print "Social notifications sent: " + str(len(notifications))
            redeemed_user_ids = list(redeemed.values_list('user', flat=True))
            unredeemed_user_ids = list(unredeemed.values_list('user', flat=True))
            all_user_ids = redeemed_user_ids + unredeemed_user_ids
            recurring_users = []
            for user_id in all_user_ids:
                if user_id in attended_user_ids:
                    recurring_users.append(user_id)
            friends_of_recurring_users = Friendship.objects.filter(user_id__in=recurring_users).values_list('friend', flat=True)
            event_statuses = EventStatus.objects.filter(event=event, user_id__in=friends_of_recurring_users).exclude(user_id__in=recurring_users).filter(Q(status=EVENT_STATUS.REDEEMED) | Q(status=EVENT_STATUS.GOING))
            print "Recurring users: " + str(len(recurring_users))
            print "All Recurring users + Friends: " + str(len(recurring_users) + len(event_statuses))
            if all_user_ids:
                print "Percentage: " + str(len(recurring_users)/float(len(all_user_ids)))
                print "Percentage with friends: " + str((len(recurring_users) + len(event_statuses))/float(len(all_user_ids)))
            print ""
            attended_user_ids.extend(all_user_ids)
        print ""
        print ""


def get_event_attendees_for_app(events):
    unredeemed = EventStatus.objects.filter(status="U", event__in=events)
    redeemed = EventStatus.objects.filter(status="R", event__in=events)
    return unredeemed, redeemed


def get_nps_score(event):
    all_responses = UserFeedback.objects.filter(sponsored_event=event)
    nps = calculate_nps(all_responses)
    return nps


def print_event_managers(market_name):
    market = Market.objects.get(name=market_name)
    managers = EventManager.objects.filter(market=market)
    for manager in managers:
        print manager.name + " " + manager.phone_number


# def update_user_statuses():
#     events = SponsoredEvent.objects.filter(start__gte=datetime.now())
#     trackers = EmailCampaignTracker.objects.filter(event__in=events, type="TL")
#     for tracker in trackers:
#         print str(tracker.event.place.name)
#         event = tracker.event
#         users = get_user_within_distance(event.place.latitude, event.place.longitude)
#         emails = Emails.objects.filter(market=event.market)
#         for user in users:
#             subject = "New open bar tickets are live"
#             description = '''Tickets are now live for our open bar at {0}. The first 30 people who buy tickets on the <a href="http://www.gethotspotapp.com">Hotspot app</a> will get their ticket for only $10. Make sure to reserve a spot ASAP!'''.format(
#                 event.place.name)
#             category = subject + "-" + str(event.id)
#             email_campaign = EmailCampaignTracker(user=user, event=event, type=EMAIL_CAMPAIGN_TYPE.TICKETS_LIVE,
#                                                           subject=subject, description=description, total_sent=1,
#                                                           category=category)
#             email_campaign.save()
#         for email in emails:
#             subject = "New open bar tickets are live"
#             description = '''Tickets are now live for our open bar at {0}. The first 30 people who buy tickets on the <a href="http://www.gethotspotapp.com">Hotspot app</a> will get their ticket for only $10. Make sure to reserve a spot ASAP!'''.format(
#                 event.place.name)
#             category = subject + "-" + str(event.id)
#             email_campaign = EmailCampaignTracker(email=email, event=event, type=EMAIL_CAMPAIGN_TYPE.TICKETS_LIVE,
#                                                   subject=subject, description=description, total_sent=1,
#                                                   category=category)
#             email_campaign.save()


def print_brand_ambassador_info():
    ambassadors = BrandAmbassador.objects.all()
    for ambassador in ambassadors:
        events = SponsoredEvent.objects.filter(market=ambassador.market, start__gte=datetime.now(), start__lte=datetime.now()+timedelta(weeks=6))
        print ambassador.name + " " + ambassador.email
        print "Promo Code: " + str(ambassador.promo_code)
        print ""
        print "Here are the links for the upcoming events:"
        for event in events:
            print "http://www.gethotspotapp.com/promo/" + str(simple_int_hash(event.id))
        print ""