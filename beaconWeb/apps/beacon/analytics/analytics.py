import datetime
from django.db.models import Q
from beaconWeb.apps.beacon.classes.foursquare_client import FoursquareClient
import braintree
from django.contrib.auth.models import User
from beaconWeb.apps.beacon.models import Payment
from beaconWeb.apps.beacon.models import Beacon
from beaconWeb.apps.beacon.models import BeaconFollow
from beaconWeb.apps.beacon.models import RegionState
from beaconWeb.apps.beacon.models import DealStatus
from beaconWeb.apps.beacon.models import DealPlace
from beaconWeb.apps.beacon.models import Deal
from beaconWeb.apps.beacon.models import Location
from beaconWeb.apps.beacon.models import Contact
from beaconWeb.apps.beacon.models import Profile
from beaconWeb.apps.beacon.models import ContactStatus
from beaconWeb.apps.beacon.models import RewardItem
from beaconWeb.apps.beacon.models import Promo
from beaconWeb.apps.beacon.models import Favorites
from beaconWeb.apps.beacon.models import NotificationTracker
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


#Price Change December 8th, 2015

#Setting
small_radius = 1
medium_radius = 5
large_radius = 25

excluded_users = [8739, 7293, 7192, 4380, 1454]
excluded_deals = [178, 207]

def user_locations(last_set_hotspot=None):
    beacons = Beacon.objects.all()
    if last_set_hotspot:
        beacons = beacons.filter(date_created__gte=last_set_hotspot)
    beacons = beacons.distinct('creator')
    beacons = beacons.select_related('creator')
    users = [beacon.creator for beacon in beacons]
    pks = [user.pk for user in users]
    users = User.objects.filter(pk__in=pks).exclude(locations=None)
    location_results = {}
    geocoder = Geocoder()
    for user in users:
            location = Location.objects.filter(user=user).latest('date_created')
            results, success = try_reverse_geocode_until_success(location.latitude, location.longitude)
            if success:
                if results[0].city not in location_results.keys():
                    location_results[results[0].city] = []
                location_results[results[0].city].append(user)
    return location_results

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


def print_user_locations(last_set_hotspot=None):
    location_results = user_locations(last_set_hotspot)
    keys = location_results.keys()
    counts = [len(users) for users in location_results.values()]
    sorted_idx = sorted_index(counts)
    sorted_idx.reverse()
    sorted_keys = [keys[idx] for idx in sorted_idx]
    for location in sorted_keys:
        print smart_format("{0} : {1}", location, len(location_results[location]))


def print_user_friends():
    friend_counts = []
    activated_users = User.objects.filter(profile__activated=True)
    for user in activated_users:
        c=Contact.objects.filter(user=user).values_list('normalized_phone', flat=True)
        num_friends = Profile.objects.filter(normalized_phone__in=c).count()
        friend_counts.append(num_friends)
    np_friend_counts = np.array(friend_counts)
    total = len(friend_counts)
    total_with_friends = 0
    for count in friend_counts:
        total_with_friends += count > 0
    mean = np.mean(np_friend_counts)
    median = np.median(np_friend_counts)
    print "activated users: {0}".format(total)
    print "activated users with friends on app: {0}".format(total_with_friends)
    print "mean friend count: {0}".format(mean)
    print "median friend count: {0}".format(median)


def num_friends(user):
    c=Contact.objects.filter(user=user).values_list('normalized_phone', flat=True)
    return Profile.objects.filter(normalized_phone__in=c).count()


def user_permissions_with_android(min_date_joined=datetime.min, max_date=datetime.now()):
    has_device = ~(Q(ios_devices=None) & Q(android_devices=None))
    has_location = ~(Q(locations=None))
    has_contacts = ~(Q(contacts=None))
    # android_user_ids = AndroidDevice.objects.all().values_list('user', flat=True)
    activated_users = User.objects.filter(profile__activated=True, date_joined__range=[min_date_joined, max_date])
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


def user_permissions_without_android(min_date_joined=datetime.min, max_date=datetime.now()):
    has_device = ~(Q(ios_devices=None) & Q(android_devices=None))
    has_location = ~(Q(locations=None))
    has_contacts = ~(Q(contacts=None))
    android_user_ids = AndroidDevice.objects.all().values_list('user', flat=True)
    activated_users = User.objects.filter(profile__activated=True, date_joined__range=[min_date_joined, max_date]).exclude(pk__in=android_user_ids)
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


def user_permissions_for_android(min_date_joined=datetime.min, max_date=datetime.now()):
    has_device = ~(Q(ios_devices=None) & Q(android_devices=None))
    has_location = ~(Q(locations=None))
    has_contacts = ~(Q(contacts=None))
    android_user_ids = AndroidDevice.objects.all().values_list('user', flat=True)
    activated_users = User.objects.filter(profile__activated=True, pk__in=android_user_ids, date_joined__range=[min_date_joined, max_date])
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


def invites_to_user_join(start=datetime.now() - timedelta(weeks=1), end=datetime.now()):
    beacon_follows = BeaconFollow.objects.filter(date_created__range=[start, end])
    return bf_to_user_join(beacon_follows)


def bf_to_user_join(beacon_follows):
    beacon_follows.select_related('user.profile', 'contact')
    joined_pks = set()
    for bf in beacon_follows:
        if bf.user and bf.date_created < bf.user.date_joined and bf.user.date_joined < bf.date_created + timedelta(weeks=1):
            joined_pks.add(bf.user.pk)
    return User.objects.filter(pk__in=joined_pks)

def viral_coefficient(end=datetime.now()):
    invites = BeaconFollow.objects.filter(date_created__lte=end).count() - Beacon.objects.filter(date_created__lte=end).count()
    user_count = User.objects.filter(date_joined__lte=end, profile__activated=True).count()
    invite_rate = invites/float(user_count)

    accepted = invites_to_user_join(datetime.min, end)
    accepted_count = len(accepted)
    acceptance_rate = accepted_count/float(invites)

    viral_coefficient = invite_rate*acceptance_rate
    print "invite rate: {0}\nacceptance rate: {1}\n viral coefficient: {2}".format(invite_rate, acceptance_rate, viral_coefficient)
    return viral_coefficient


def top_users(min_invites):
    #get number of hotspots set for each user
    users = User.objects.all()
    beacon_counts = []
    useridx=0
    for user in users:
        count = 0
        beacons = Beacon.objects.filter(creator=user)
        #only count hotspots with min number of invites
        if beacons.count() > 0:
            for beacon in beacons:
                count += BeaconFollow.objects.filter(beacon=beacon).count() > min_invites
        beacon_counts.append(count)
    sorted_indexes = sorted_index(beacon_counts)
    sorted_indexes.reverse()
    users_sorted = []
    for idx in sorted_indexes:
        users_sorted.append((users[idx], beacon_counts[idx]))
    return users_sorted


def print_top_users(min_invites=2):
    users = top_users(min_invites)[0:50]
    for user in users:
        print smart_format("{0} {1} : {2}", user[0].first_name, user[0].last_name, user[1])
    print '\n\n\n'
    for user in users:
        beacon_descriptions = Beacon.objects.filter(creator=user[0]).values_list('description', flat=True)
        print '-------'
        print smart_format("{0} {1} : {2}", user[0].first_name, user[0].last_name, beacon_descriptions)
        print '-------'


def active_users(start=datetime.now() - timedelta(weeks=4), end=datetime.now()):
#    users who have set hotspots and invited at least one person or viewed hotspot
    hotspots = Beacon.objects.filter(date_created__range=[start, end]).annotate(num_invites=Count('beacon_follows')).filter(num_invites__gt=1)
    saw_invite = BeaconFollow.objects.filter(beacon__in=hotspots, saw_invite=True).exclude(user=None)
    user_pks = set()
    [user_pks.add(o) for o in hotspots.values_list('creator__pk', flat=True)]
    [user_pks.add(o) for o in saw_invite.values_list('user__pk', flat=True)]
    users = User.objects.filter(pk__in=list(user_pks))
    #exclude friends of jeff and jas
    jas = User.objects.get(username='5413359388')
    jeff = User.objects.get(username='6176337532')
    either = Q(user=jeff) | Q(user=jas)
    friend_numbers = Contact.objects.filter(either).values_list('normalized_phone', flat=True)
    friends_excluded = users.exclude(profile__normalized_phone__in=friend_numbers)
    print "total: {0}\nexluding friends: {1}".format(users.count(), friends_excluded.count())
    return users, friends_excluded


def sorted_index(l):
    return [i[0] for i in sorted(enumerate(l), key=lambda x:x[1])]


def csv_for_user_feedback():
    jas = User.objects.get(username='5413359388')
    jeff = User.objects.get(username='6176337532')
    jas_friends = list(Contact.objects.filter(user=jas).values_list('normalized_phone', flat=True))
    jeff_friends = list(Contact.objects.filter(user=jeff).values_list('normalized_phone', flat=True))
    excluded = jas_friends + jeff_friends
    users = User.objects.filter(profile__activated=True).exclude(profile__normalized_phone__in=excluded)
    odd = []
    even = []
    for u in users:
        if u.pk%2:
            odd.append(u.pk)
        else:
            even.append(u.pk)
    jas_users = User.objects.filter(pk__in=even)
    jeff_users = User.objects.filter(pk__in=odd)
    create_user_csv(jas_users, 'jas.csv')
    create_user_csv(jeff_users, 'jeff.csv')


def user_classification(num_hotspots, num_friends, invites_sent):
    classification = 'inactive'
    if num_hotspots > 2:
        classification = 'power'
    elif num_hotspots >= 1:
        classification = 'moderate'
    return classification


def create_user_csv(users=User.objects.filter(profile__activated=True), filename="test.csv"):
    pks = [u.pk for u in users]
    names = [smart_format("{0} {1}", u.first_name, u.last_name) for u in users]
    email = [u.email for u in users]
    set_hotspots = []
    friends = []
    invites_sent = []
    invites_received = []
    classifications = []
    users.select_related('created_hotspots', 'contacts', 'sent_invites')
    for u in users:
        hotspot_count = u.created_hotspots.count()
        friend_count = num_friends(u)
        invites_sent_count = u.sent_invites.count()
        invites_received_count = u.received_invites.count()
        classification = user_classification(hotspot_count, friend_count, invites_sent_count)
        set_hotspots.append(hotspot_count)
        friends.append(friend_count)
        invites_sent.append(invites_sent_count)
        invites_received.append(invites_received_count)
        classifications.append(classification)

    attribute_names = ['pk', 'name', 'email', 'classification', 'set hotspots', 'friends', 'sent invites', 'received invites']
    create_csv(attribute_names, filename, pks, names, email, classifications, set_hotspots, friends, invites_sent, invites_received)


def create_csv(attribute_names, filename="test.csv", *args):
    data = []
    for i in range(len(args)):
        data.append([attribute_names[i]] + args[i])

    data = zip(*data)
    import csv
    with open(filename, 'w') as fp:
        a = csv.writer(fp, delimiter=',')
        a.writerows(data)


def get_user_within_distance(lat, lng, distance=20, max_date = datetime.now(), min_date = datetime(2014, 9, 1)):
    lat_range = [lat-0.3, lat+0.3]
    lng_range = [lng-0.3, lng+0.3]
    users_in_location = Location.objects.filter(latitude__range=lat_range, longitude__range=lng_range, date_created__range=[min_date, max_date]).exclude(user__in=excluded_users).values_list('user', flat=True)
    # users_in_location = []
    # for location in locations:
    #     dist = distance_between_two_points(lat, lng, location.latitude, location.longitude)
    #     if dist < distance:
    #         if location.user_id not in users_in_location:
    #             users_in_location.append(location.user_id)
    user_obj = User.objects.filter(pk__in=users_in_location).exclude(pk__in=excluded_users)
    return user_obj


def get_total_new_haven_users():
    today = datetime.now().replace(hour=23, minute=59, second=0, microsecond=0)
    users = get_user_within_distance(41.311272, -72.932041, 1, today, datetime(2014, 9, 1))
    print "Total Users: " + str(len(users))
    # for user in users:
    #     print user.first_name + " " + user.last_name + " " + user.email
    return len(users)

def highest_user_number(lat, lng, distance):
    locations = Location.objects.all()
    users_in_location = []
    for location in locations:
        dist = distance_between_two_points(lat, lng, location.latitude, location.longitude)
        if dist < distance:
            if location.user_id not in users_in_location:
                users_in_location.append(location.user_id)
    user_obj = User.objects.filter(pk__in=users_in_location).exclude(pk__in=excluded_users)
    return user_obj

def get_deal_places_in_area(lat, lng, distance):
    places = DealPlace.objects.all()
    places_in_area = []
    for place in places:
        dist = distance_between_two_points(place.latitude, place.longitude, lat, lng)
        if dist < distance:
            places_in_area.append(place.id)
    return places_in_area

def get_location_info():
    place_ids = get_deal_places_in_area(41.300093, -72.9262206, 5)
    regions_entered = RegionState.objects.filter(place_id__in=place_ids).exclude(user_id__in=excluded_users)
    notifications = regions_entered.filter(showed_notification=True).distinct('user')
    return str(len(regions_entered)), str(len(notifications))


def get_deal_hotspots(deal_lat, deal_lng, distance, min_date=datetime.now()-timedelta(weeks=100), max_date=datetime.now()):
    excluded_beacons = Beacon.objects.filter(creator_id__in=excluded_users)
    non_yale_deals = [26]
    # excluded_beacons = deal_status.values_list('beacon_id', flat=True).distinct()
    hotspot_ids = DealStatus.objects.values_list('beacon_id', flat=True).distinct().exclude(beacon__in=excluded_beacons).exclude(deal_id__in=non_yale_deals)
    hotspots = Beacon.objects.filter(pk__in=hotspot_ids, time__range=[min_date, max_date]).exclude(cancelled=True)
    hotspots_within_distance = []
    for hotspot in hotspots:
        dist = distance_between_two_points(hotspot.latitude, hotspot.longitude, deal_lat, deal_lng)
        if dist < distance:
            hotspots_within_distance.append(hotspot)
    #hotspots = Beacon.objects.filter(pk__in=hotspot_ids)
    return hotspots_within_distance


def get_percentage_joined(all_invites):
    contact_numbers = []
    for invite in all_invites:
        if invite.contact:
            if invite.contact.normalized_phone not in contact_numbers:
                contact_numbers.append(invite.contact.normalized_phone)
    total_non_users_invited = len(contact_numbers)
    users_joined = Profile.objects.filter(normalized_phone__in=contact_numbers)
    return float(len(users_joined))/total_non_users_invited


def get_unique_invite_length(total_invites):
    phone_numbers = []
    for invite in total_invites:
        if invite.user:
            phone_numbers.append(invite.user.profile.normalized_phone)
        else:
            phone_numbers.append(invite.contact.normalized_phone)
    return len(set(phone_numbers))


def get_deal_stats():
    users = get_user_within_distance(41.300093,-72.9262206, 20)
    location_entrances, location_notifications = get_location_info()
    hotspots = get_deal_hotspots(41.300093,-72.9262206, 5)
    total_invites = BeaconFollow.objects.filter(beacon__in=hotspots).exclude(invited_by=None)
    total_invites_before = BeaconFollow.objects.filter(beacon__in=hotspots, date_created__lt=datetime(2014, 10, 11)).exclude(invited_by=None)
    total_invites_after =  BeaconFollow.objects.filter(beacon__in=hotspots, date_created__gte=datetime(2014, 10,11)).exclude(invited_by=None)
    invitations_to_contacts_before = len(total_invites_before.filter(user=None))
    invitations_to_contacts_after = len(total_invites_after.filter(user=None))
    invites_read = total_invites.filter(saw_invite=True)
    invites_going = total_invites.all().exclude(state="I")
    users_joined_before = bf_to_user_join(total_invites_before)
    users_joined_after = bf_to_user_join(total_invites_after)
    percentage_joined_before = len(users_joined_before)/float(len(total_invites_before))
    percentage_joined_after = len(users_joined_after)/float(len(total_invites_after))
    hotspots_set_from_local_notifications = get_hotspots_set_from_local_notification(hotspots)
    print "Total users: " + str(len(users))
    print "Location entrances: " + location_entrances
    print "Location notifications: " + location_notifications
    print "Hotspots set: " + str(len(hotspots))
    print "Total invites: " + str(len(total_invites))
    print "Total invites (before): " + str(len(total_invites_before))
    print "Percent to Contacts (before): " + str(invitations_to_contacts_before/float(len(total_invites_before)))
    print "Total invites (after): " + str(len(total_invites_after))
    print "Percent to Contacts (after): " + str(invitations_to_contacts_after/float(len(total_invites_after)))
    print "Unique invites: " + str(get_unique_invite_length(total_invites))
    print "Avg Invites/Hotspot: " + str(float(len(total_invites))/len(hotspots))
    print "Percentage of invites read: " + str(float(len(invites_read))/len(total_invites))
    print "Percentage of RSVP: " + str(float(len(invites_going))/len(total_invites))
    print "Percentage redeemed: "
    print "Users joined before: " + str(len(users_joined_before))
    print "Users joined after: " + str(len(users_joined_after))
    print "Percentage joined (before experiment): " + str(percentage_joined_before)
    print "Percentage joined (after experiment): " + str(percentage_joined_after)
    print "Percent of Hotpsots from Local Notifications: " + str(len(hotspots_set_from_local_notifications)/float(len(hotspots)))
    print "Local Notifications to Hotspot: " + str(get_local_notification_to_hotspot_percentage())

def get_users_in_new_haven():
    today = datetime.now().replace(hour=23, minute=59, second=0, microsecond=0)
    users = get_user_within_distance(41.311272, -72.932041, 1, today)
    print "Total Users: " + str(len(users))
    # for user in users:
    #     print user.first_name + " " + user.last_name + " " + user.email
    return len(users)


def hotspot_breakdown_by_business():
    hotspots = get_deal_hotspots(41.300093,-72.9262206, 5)
    total_deals = len(hotspots)
    deals = DealStatus.objects.filter(beacon__in=hotspots).distinct('beacon')
    deals_at_places = {}
    for deal_status in deals:
        if deal_status.deal.place.name in deals_at_places.keys():
            deals_at_places[deal_status.deal.place.name].append(deal_status.beacon_id)
        else:
            deals_at_places[deal_status.deal.place.name] = [deal_status.beacon_id]
    for key, value in deals_at_places.iteritems():
        print key + ": " + str((len(value)/float(total_deals))*100) + "%"


def last_day(d, day_name):
    days_of_week = ['sunday','monday','tuesday','wednesday',
                        'thursday','friday','saturday']
    target_day = days_of_week.index(day_name.lower())
    delta_day = target_day - d.isoweekday()
    if delta_day >= 0: delta_day -= 7 # go back 7 days
    return d + timedelta(days=delta_day)


def user_growth(number_of_weeks):
    today = datetime.now()
    last_sunday = last_day(today, "Sunday")
    users = get_user_within_distance(41.300093,-72.9262206, 5)
    week = 0
    last_week = 0
    while week < number_of_weeks:
        min_date = last_sunday - timedelta(weeks=(week + 1), days=-1)
        max_date = last_sunday - timedelta(weeks=week)
        users_joined = users.filter(date_joined__range=[min_date, max_date])
        if last_week == 0:
            percentage_string = ""
        else:
            percentage_string = " "
        print str(len(users_joined)) + percentage_string
        week += 1
        last_week = len(users_joined)


def get_seven_day_engagement(hotspots, days_ago):
    today = datetime.now().replace(hour=23, minute=59, second=0, microsecond=0)
    max_date = today - timedelta(days=days_ago)
    min_date = max_date - timedelta(days=7)
    active_users = len(get_user_within_distance(41.311272, -72.932041, 1, max_date, max_date - timedelta(weeks=4)))
    hotspots_within_last_seven_days = hotspots.filter(date_created__gt=min_date, date_created__lte=max_date)
    if active_users != 0:
        return round((len(hotspots_within_last_seven_days)/float(active_users))*100, 1)
    else:
        return 0


def get_venues_within_distance(lat, lng, radius=medium_radius):
    venues_within_distance = []
    venues = DealPlace.objects.all()
    for venue in venues:
        distance = distance_between_two_points(lat, lng, venue.latitude, venue.longitude)
        if distance < radius:
            venues_within_distance.append(venue)
    filtered_venue_ids = Deal.objects.filter(place__in=venues_within_distance, active=True, in_app_payment=True).values_list('place_id', flat=True)
    venues = DealPlace.objects.filter(pk__in=filtered_venue_ids)
    return venues

def get_venue_stats(venue_id, min_date=datetime.now() - timedelta(weeks=4), max_date=datetime.now()):
    venue_stats = {}
    venue = DealPlace.objects.get(pk=venue_id)
    hotspots = get_hotspots_at_venue(venue, min_date, max_date)
    venue_hotspots = len(hotspots)
    total_hotspots = len(get_deal_hotspots(41.300093, -72.9262206, 5, min_date, max_date))
    active_users_min_date = len(get_user_within_distance(venue.latitude, venue.longitude, small_radius, min_date))
    active_users_max_date = len(get_user_within_distance(venue.latitude, venue.longitude, small_radius, max_date))
    venue_stats['active_users_max_date'] = active_users_max_date
    venue_stats['active_users_min_date'] = active_users_min_date
    venue_stats['active_user_growth'] = 0 if active_users_min_date == 0 else str(int(((active_users_max_date-active_users_min_date)/float(active_users_min_date))*100))+"%"
    venue_stats['total_hotspots'] = venue_hotspots
    venue_stats['total_invites_sent'] = len(BeaconFollow.objects.filter(beacon__in=hotspots))
    venue_stats['total_rsvp'] = len(BeaconFollow.objects.filter(beacon__in=hotspots).exclude(state="I"))
    venue_stats['total_redemptions'] = len(DealStatus.objects.filter(beacon__in=hotspots, deal_status="R"))
    venue_stats['total_hotspots_at_all_venues'] = total_hotspots
    venue_stats['share_of_all_hotspots'] = 0 if total_hotspots == 0 else str(int((venue_hotspots/float(total_hotspots))*100))+"%"
    return venue_stats

def generate_csv_for_all_venues(min_date, max_date):
    attribute_dict = {}
    attribute_names = get_venue_stats(1).keys()
    attribute_names.insert(0, "Venue Name")
    for attribute in attribute_names:
        attribute_dict[attribute] = []
    places = DealPlace.objects.all()
    for place in places:
        venue_stats = get_venue_stats(place.id, min_date, max_date)
        for attribute in attribute_names:
            if attribute == "Venue Name":
                attribute_dict[attribute].append(place.name)
            else:
                attribute_dict[attribute].append(venue_stats[attribute])
        create_csv(attribute_names, "venue_performance.csv", attribute_dict[attribute_names[0]], attribute_dict[attribute_names[1]], attribute_dict[attribute_names[2]], attribute_dict[attribute_names[3]], attribute_dict[attribute_names[4]], attribute_dict[attribute_names[5]], attribute_dict[attribute_names[6]], attribute_dict[attribute_names[7]], attribute_dict[attribute_names[8]])

def get_hotspots_at_venue(venue, min_date, max_date):
    deals = Deal.objects.filter(place__in=[venue])
    deal_status = DealStatus.objects.filter(user_id__in=excluded_users)
    excluded_beacons = deal_status.values_list('beacon_id', flat=True).distinct()
    hotspot_ids = DealStatus.objects.values_list('beacon_id', flat=True).distinct().filter(deal__in=deals, start__range=[min_date, max_date]).exclude(beacon_id__in=excluded_beacons)
    unique_hotspots = Beacon.objects.filter(pk__in=hotspot_ids).exclude(cancelled=True)
    return unique_hotspots


def get_hotspot_querylist():
    hotspot_ids = []
    hotspots = get_deal_hotspots(41.300093,-72.9262206, 5)
    for hotspot in hotspots:
        hotspot_ids.append(hotspot.id)
    hotspot_querylist = Beacon.objects.filter(pk__in=hotspot_ids)
    return hotspot_querylist

def get_engagement_labels_and_data(days):
    label = []
    data = []
    hotspots = get_hotspot_querylist()
    i = 0
    while i < days + 1:
        data.insert(0, get_seven_day_engagement(hotspots, i))
        label.append(days - i)
        i += 1
    return label, data

def get_hotspots_set_from_local_notification(hotspots):
    local_notification_hotspots = []
    for hotspot in hotspots:
        min_time = hotspot.date_created - timedelta(hours=4)
        max_time = hotspot.date_created
        if RegionState.objects.filter(user=hotspot.creator, showed_notification=True, date_created__gte=min_time, date_created__lte=max_time).exists():
            local_notification_hotspots.append(hotspot)
    return local_notification_hotspots


def get_local_notification_to_hotspot_percentage():
    successful_local_notifications = []
    venues = get_venues_within_distance(41.300093,-72.9262206)
    local_notifications = RegionState.objects.filter(place__in=venues, showed_notification=True).exclude(user__in=excluded_users)
    for local_notification in local_notifications:
        max_time = local_notification.date_created + timedelta(hours=4)
        min_time = local_notification.date_created
        if Beacon.objects.filter(creator = local_notification.user,date_created__gte=min_time, date_created__lte=max_time).exists():
            successful_local_notifications.append(local_notification)
    return len(successful_local_notifications)/float(len(local_notifications))


def get_push_rsvp():
    hotspots = get_deal_hotspots(41.300093,-72.9262206, 5)
    push_users = User.objects.all().exclude(android_devices=None,ios_devices=None)
    total_bf = BeaconFollow.objects.filter(beacon__in=hotspots, user__in=push_users, contact=None).exclude(invited_by_id__isnull=True)
    rsvp_bf = total_bf.exclude(state="I")
    read_bf = total_bf.filter(saw_invite=True)
    rsvp_percentage = len(rsvp_bf)/float(len(total_bf))
    read_percentage = len(read_bf)/float(len(total_bf))
    return read_percentage, rsvp_percentage

def get_sms_user_rsvp():
    hotspots = get_deal_hotspots(41.300093,-72.9262206, 5)
    non_push_users = User.objects.filter(android_devices=None,ios_devices=None)
    total_bf = BeaconFollow.objects.filter(beacon__in=hotspots, user__in=non_push_users, contact=None).exclude(invited_by_id__isnull=True)
    rsvp_bf = total_bf.exclude(state="I")
    read_bf = total_bf.filter(saw_invite=True)
    rsvp_percentage = len(rsvp_bf)/float(len(total_bf))
    read_percentage = len(read_bf)/float(len(total_bf))
    return read_percentage, rsvp_percentage


def get_sms_non_user_rsvp():
    hotspots = get_deal_hotspots(41.300093,-72.9262206, 5)
    total_bf = BeaconFollow.objects.filter(beacon__in=hotspots, user=None).exclude(invited_by_id__isnull=True)
    rsvp_bf = total_bf.exclude(state="I")
    read_bf = total_bf.filter(saw_invite=True)
    rsvp_percentage = len(rsvp_bf)/float(len(total_bf))
    read_percentage = len(read_bf)/float(len(total_bf))
    return read_percentage, rsvp_percentage


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


def get_contact_status_yes_responses(contact_statuses):
    yes_contact_statuses = []
    for contact_status in contact_statuses:
        if contact_status.sms_response == 'Y':
            yes_contact_statuses.append(contact_status)
    return yes_contact_statuses


def get_contact_status_link_clicks(contact_statuses):
    link_clicks_contact_statuses = []
    for contact_status in contact_statuses:
        if contact_status.link_clicked:
            link_clicks_contact_statuses.append(contact_status)
    return link_clicks_contact_statuses


def get_contact_status_stats(max_date=datetime.now(), min_date=datetime(2015, 5, 18)):
    excluded_beacons = Beacon.objects.filter(creator_id__in=excluded_users)
    deals = Deal.objects.filter(active=True, in_app_payment=True)
    hotspot_ids = DealStatus.objects.filter(deal__in=deals).values_list('beacon_id', flat=True).distinct().exclude(beacon__in=excluded_beacons)
    hotspots = Beacon.objects.filter(pk__in=hotspot_ids, time__range=[min_date, max_date]).exclude(cancelled=True)
    deal_statuses = DealStatus.objects.filter(deal__in=deals).exclude(beacon__in=excluded_beacons)
    total_invites = BeaconFollow.objects.filter(beacon__in=hotspots).exclude(invited_by=None)
    contact_statuses = filter_contact_status(max_date, min_date, deal_statuses)
    yes_responses = get_contact_status_yes_responses(contact_statuses)
    link_click = get_contact_status_link_clicks(contact_statuses)
    registrations = get_contact_status_registration(contact_statuses)
    print "Total Invitations Sent: " + str(len(total_invites))
    print "Total Sent to Contacts: " + str(len(contact_statuses))
    print "Contact RSVP: " + str(len(yes_responses))
    print "Contact Link Click: " + str(len(link_click))
    print "Registrations: " + str(len(registrations))
    if len(contact_statuses) == 0 or len(total_invites) == 0:
        print "Contact to Reg Rate: 0"
        print "Invitation to Reg Rate: 0"
    else:
        print "Contact to Reg Rate: " + str(len(registrations)/(float(len(contact_statuses))))
        print "Invitation to Reg Rate: " + str(len(registrations)/(float(len(total_invites))))


def get_power_users():
    users = get_user_within_distance(41.311272, -72.932041, 10, datetime.now(), datetime(2014, 9, 1))
    power_users = []
    for user in users:
        if Beacon.objects.filter(creator=user).count() > 2:
            power_users.append(user)
            return power_users


# def get_total_users(min_date=datetime(2014, 9, 1), max_date= datetime.now()):
#     deals = Deal.objects.filter(active=True, in_app_payment=True)
#     total_users = []
#     # for deal in deals:
#     #     lat = deal.place.latitude
#     #     lng = deal.place.longitude
#     users = get_user_within_distance(lat, lng, 20, max_date, min_date)
#     #     total_users.extend(users)
#     # return set(total_users)



def get_weekly_user_growth(start_date = datetime.now(), number_of_weeks=10):
    users = get_total_users()
    user_qs = User.objects.filter(pk__in=[x.pk for x in users])
    for week in range(0, number_of_weeks):
        today = start_date - timedelta(weeks=week)
        last_week = start_date - timedelta(weeks=week + 1)
        total_users_last_week = user_qs.filter(date_joined__lt=last_week)
        new_users = user_qs.filter(date_joined__gte=last_week, date_joined__lt=today)
        print "New Users: " + str(len(new_users))
        print "Percentage Growth: " + str(len(new_users)*100/float(len(total_users_last_week)))


def get_weekly_actives(start_date = datetime.now(), number_of_weeks=10):
    users = get_total_users()
    android_user_ids = AndroidDevice.objects.all().values_list('user', flat=True)
    user_qs = User.objects.filter(pk__in=[x.pk for x in users]).exclude(pk__in=android_user_ids)
    venues = DealPlace.objects.all()
    deals = Deal.objects.filter(place__in=venues)
    excluded_beacons = Beacon.objects.filter(creator_id__in=excluded_users)
    hotspot_ids = DealStatus.objects.filter(deal__in=deals, in_app_payment=True, active=True).values_list('beacon_id', flat=True).distinct().exclude(beacon__in=excluded_beacons)
    deal_statuses = DealStatus.objects.filter(beacon_id__in=hotspot_ids)
    for week in range(0, number_of_weeks):
        today = start_date - timedelta(weeks=week)
        last_week = start_date - timedelta(weeks=week + 1)
        two_weeks_ago = start_date - timedelta(weeks=week + 2)
        total_users_to_date = user_qs.filter(date_joined__lt=today)
        users = Location.objects.filter(date_created__gte=last_week, date_created__lt=today, user__in=user_qs).values_list('user', flat=True).distinct()
        last_week_users = Location.objects.filter(date_created__gte=two_weeks_ago, date_created__lt=last_week, user__in=user_qs).values_list('user', flat=True).distinct()
        percentage_increase = (len(users) - len(last_week_users))/float(len(last_week_users))
        hotspots = Beacon.objects.filter(pk__in=hotspot_ids, date_created__lt=today, date_created__gte=last_week).exclude(cancelled=True)
        this_week_invites = BeaconFollow.objects.filter(beacon__in=hotspots).exclude(invited_by=None)
        contact_statuses = filter_contact_status(today, last_week)
        registrations = get_contact_status_registration(contact_statuses)
        invitation_per_weekly_active = float(len(this_week_invites))/len(users)
        conversion_rate = len(registrations)/(float(len(this_week_invites)))
        users_from_growth = User.objects.filter(date_joined__gte=last_week, date_joined__lt=today, pk__in=users)
        # viral_growth = (len(this_week_invites) * conversion_rate)/len(last_week_users)
        viral_growth = (len(registrations)/float(len(last_week_users)))
        hotspots_set = get_hotspots_set(last_week, today)
        print "Weekly Actives: " + str(len(users))
        # print "Retained Percentage Increase: " + str((len(users) - len(last_week_users) - len(users_from_growth))/float(len(last_week_users)))
        print "Total Percentage Increase: " + str(percentage_increase)
        print "Invitations: " + str(len(contact_statuses))
        # print "Invitations/Weekly Actives: " + str(invitation_per_weekly_active)
        print "Conversion Rate: " + str(len(registrations)/(float(len(contact_statuses))))
        print "Viral Growth: " + str(viral_growth)
        # print "Hotspots Set: " + str(len(hotspots_set))
        print "Total users: " + str(len(total_users_to_date))
        print "Percent: " + str(float(len(users))/len(total_users_to_date))
        # print "Hotspots/Users: " + str(len(hotspots_set)/float(len(users)))
        # print "Non-Viral Growth: " + str(len(users_from_non_viral_growth)/float(len(last_week_users)))
        print ""


def get_weekly_actives_within_distance(lat=47.6369484, lng=-122.3625873, distance=10, start_date = datetime.now(), number_of_weeks=10):
    users = get_user_within_distance(lat, lng, distance)
    venues = get_venues_within_distance(lat, lng, distance)
    deals = Deal.objects.filter(place__in=venues, active=True, in_app_payment=True)
    android_user_ids = AndroidDevice.objects.all().values_list('user', flat=True)
    user_qs = User.objects.filter(pk__in=[x.pk for x in users]).exclude(pk__in=android_user_ids)
    excluded_beacons = Beacon.objects.filter(Q(creator_id__in=excluded_users) | Q(creator_id__in=android_user_ids))
    hotspot_ids = DealStatus.objects.filter(deal__in=deals).values_list('beacon_id', flat=True).distinct().exclude(beacon__in=excluded_beacons)
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
        contact_statuses = filter_contact_status(today, last_week)
        # converted_users = get_converted_users(total_users_to_date, today)
        # promo_code_registrations = get_promo_code_registrations(last_week, today)
        viral_registrations = get_contact_status_registration(contact_statuses)
        additional_promo_code_registrations = get_promo_code_registrations(last_week, today, viral_registrations)
        registrations = len(viral_registrations) + len(additional_promo_code_registrations)
        in_bar_registrations = get_drink_card_reward_items(last_week, today)
        invitation_per_weekly_active = float(len(this_week_invites))/len(users)
        invitation_per_hotspot = float(len(this_week_invites))/len(hotspots)
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
            conversion_rate = str(len(viral_registrations)/(float(len(contact_statuses))))
        else:
            conversion_rate = "0"
        percent_open_radius = get_percent_open_radius(lat, lng, today, last_week)
        users_with_follows = get_users_with_follows(today)
        if len(users_with_follows):
            average_follows_per_user = len(Favorites.objects.filter(active=True, user_id__in=users_with_follows))/float(len(users_with_follows))
        else:
            average_follows_per_user = 0
        print "Weekly Actives: " + str(len(users))
        print "Weekly Actives Without New Users: " + str(len(users) - new_users_this_week)
        # print "Retained Percentage Increase: " + str((len(users) - len(last_week_users) - len(users_from_growth))/float(len(last_week_users)))
        print "Total User Percentage Increase: " + str(percentage_increase)
        print "Invitations Sent: " + str(len(contact_statuses))
        # print "Invitations/Weekly Actives: " + str(invitation_per_weekly_active)
        print "Conversion Rate: " + conversion_rate
        print "(Viral) Registration: " + str(registrations)
        print "In-Venue Registration: " + str(len(in_bar_registrations))
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
        print "% Opened in Radius: " + str(percent_open_radius)
        print "Revenue: " + str(revenue_this_week)
        # print "Revenue/User: " + str(revenue_this_week/float(len(total_users_to_date)))
        print "Projected ARPU: " + str((revenue_this_week * 52)/float(len(total_users_to_date)))
        # print "Number of Users w/Follows: " + str(len(users_with_follows))
        print "Number of Users w/Follows as %: " + str(float(len(users_with_follows)*100)/len(total_users_to_date))
        print "Average Follows/User: " + str(average_follows_per_user)
        print ""


def get_all_users_with_redemption(date=datetime.now()):
    lat=47.6369484
    lng=-122.3625873
    distance=10
    users = get_user_within_distance(lat, lng, distance)
    user_qs = User.objects.filter(pk__in=[x.pk for x in users])
    total_users_to_date = user_qs.filter(date_joined__lt=date)
    users_with_redemptions = get_users_with_redemptions(total_users_to_date, date)
    return users_with_redemptions


def get_active_users(min_date=datetime.now()-timedelta(weeks=1), max_date=datetime.now(), lat=47.6369484, lng=-122.3625873, distance=10):
    users = get_user_within_distance(lat, lng, distance)
    user_qs = User.objects.filter(pk__in=[x.pk for x in users])
    users_to_exclude = User.objects.filter(date_joined__gte=min_date, date_joined__lt=max_date)
    active_users = Location.objects.filter(date_created__gte=min_date, date_created__lt=max_date, user__in=user_qs).exclude(user__in=users_to_exclude).values_list('user', flat=True).distinct()
    return active_users

def get_weekly_actives_with_android(lat=47.6369484, lng=-122.3625873, distance=10, start_date = datetime.now(), number_of_weeks=10):
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
        in_bar_registrations = get_drink_card_reward_items(last_week, today)
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
        print "In-Venue Registration: " + str(len(in_bar_registrations))
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


def _redeemer_stats(lat=47.6369484, lng=-122.3625873, distance=10, start_date = datetime.now(), number_of_weeks=10):
    users = get_user_within_distance(lat, lng, distance)
    venues = get_venues_within_distance(lat, lng, distance)
    deals = Deal.objects.filter(place__in=venues, active=True, in_app_payment=True)
    users_in_distance = User.objects.filter(pk__in=[x.pk for x in users])
    user_qs = get_users_with_redemptions(users_in_distance, datetime.now())
    excluded_beacons = Beacon.objects.filter(creator_id__in=excluded_users)
    hotspot_ids = DealStatus.objects.filter(deal__in=deals).values_list('beacon_id', flat=True).distinct().exclude(beacon__in=excluded_beacons).exclude(deal__in=excluded_deals)
    for week in range(0, number_of_weeks):
        today = start_date - timedelta(weeks=week)
        last_week = start_date - timedelta(weeks=week + 1)
        two_weeks_ago = start_date - timedelta(weeks=week + 2)
        users = Location.objects.filter(date_created__gte=last_week, date_created__lt=today, user__in=user_qs).values_list('user', flat=True).distinct()
        total_users_to_date = get_users_with_redemptions(user_qs, today)
        total_users_last_week = get_users_with_redemptions(user_qs, last_week)
        new_users_this_week = len(total_users_to_date) - len(total_users_last_week)
        percentage_increase = new_users_this_week/float(len(total_users_last_week))
        hotspots = Beacon.objects.filter(pk__in=hotspot_ids, date_created__lt=today, date_created__gte=last_week).exclude(cancelled=True)
        contact_statuses = filter_contact_status_by_referrer(total_users_to_date, today, datetime(2014, 9, 1))
        viral_registrations = get_contact_status_registration(contact_statuses)
        additional_promo_code_registrations = get_promo_code_registrations_for_redeemers(users, datetime(2014, 9, 1), today, viral_registrations)
        registrations = viral_registrations + additional_promo_code_registrations
        new_users_from_viral = total_users_to_date.filter(pk__in=[x.pk for x in registrations]).exclude(pk__in=[x.pk for x in total_users_last_week])
        viral_growth = (len(new_users_from_viral)/float(len(total_users_last_week)))
        paid_deal_statuses = DealStatus.objects.filter(beacon__in=hotspots)
        paid_redemptions = len(paid_deal_statuses.filter(deal_status=DEAL_STATUS.REDEEMED).exclude(payment_authorization="REWARD"))
        reward_redemptions = len(paid_deal_statuses.filter(payment_authorization="REWARD", deal_status=DEAL_STATUS.REDEEMED))
        total_redemptions = paid_redemptions + reward_redemptions
        revenue_this_week = 0
        for deal_status in paid_deal_statuses:
            if deal_status.payment:
                if deal_status.payment.is_submitted:
                    revenue_this_week = revenue_this_week + deal_status.deal.item_price
        low_gross_profect_projection, high_gross_profit_projection = get_gross_profit(hotspot_ids, today)
        # percent_open_radius = get_percent_open_radius(lat, lng, today, last_week)
        # users_with_follows = get_users_with_follows(today)
        # if len(users_with_follows):
        #     average_follows_per_user = len(Favorites.objects.filter(active=True, user_id__in=users_with_follows))/float(len(users_with_follows))
        # else:
        #     average_follows_per_user = 0
        print "Weekly Actives: " + str(len(users))
        print "Weekly Actives Without New Users: " + str(len(users) - new_users_this_week)
        print "Total User Percentage Increase: " + str(percentage_increase)
        print "(Viral) Registration: " + str(len(new_users_from_viral))
        print "Viral Growth: " + str(viral_growth)
        # print "Invitations/Hotspot: " + str(invitation_per_hotspot)
        print "Paid Redemptions: " + str(paid_redemptions)
        print "Reward Redemptions: " + str(reward_redemptions)
        print "Total Redemptions: " + str(total_redemptions)
        # print "Hotspots Set: " + str(len(hotspots))
        print "Total users: " + str(len(total_users_to_date))
        print "Percent: " + str(float(len(users))/len(total_users_to_date))
        print "Percent without New Users: " + str(float(len(users) - new_users_this_week)/(len(total_users_to_date) - new_users_this_week))
        print "Low Gross Profit/Year/User: " + str(low_gross_profect_projection/float(len(total_users_to_date)))
        print "High Gross Profit/Year/User: " + str(high_gross_profit_projection/float(len(total_users_to_date)))
        print "Revenue: " + str(revenue_this_week)
        print "Projected ARPU: " + str((revenue_this_week * 52)/float(len(total_users_to_date)))
        print "Average Friends/User: "  + str(get_average_number_of_friends_on_hotspot(total_users_to_date))
        print ""


def get_users_with_redemptions(users, today):
    user_ids = DealStatus.objects.filter(user__in=users, date_created__lte=today, deal_status=DEAL_STATUS.REDEEMED).values_list('user', flat=True).exclude(deal__in=excluded_deals)
    users_with_redemptions = User.objects.filter(pk__in=user_ids)
    return users_with_redemptions


def get_gross_profit(hotspot_ids, today):
    min_date = today - timedelta(days=30)
    hotspots = Beacon.objects.filter(pk__in=hotspot_ids, date_created__lt=today, date_created__gte=min_date).exclude(cancelled=True)
    deal_statuses = DealStatus.objects.filter(beacon__in=hotspots)
    paid_redemptions = deal_statuses.filter(deal_status=DEAL_STATUS.REDEEMED).exclude(payment_authorization="REWARD")
    reward_redemptions = deal_statuses.filter(payment_authorization="REWARD", deal_status=DEAL_STATUS.REDEEMED)
    filtered_reward_redemptions = []
    for redemption in reward_redemptions:
        if DealStatus.objects.filter(user=redemption.user, date_created__lt=redemption.date_created, deal_status=DEAL_STATUS.REDEEMED).exists():
            filtered_reward_redemptions.append(redemption)
    low_gross_profit = (len(paid_redemptions) * 12)
    high_gross_profit = (len(paid_redemptions) + len(filtered_reward_redemptions)) * 12
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


def get_hotspots_set(min_date, max_date):
    venues = DealPlace.objects.all()
    deals = Deal.objects.filter(place__in=venues)
    beacons = Beacon.objects.all().exclude(creator__in=excluded_users)
    unique_deal_statuses = DealStatus.objects.filter(deal__in=deals, beacon__in=beacons, date_created__gte=min_date, contact=None, date_created__lte=max_date).distinct("beacon")
    return unique_deal_statuses

def get_users_in_new_markets():
    all_users = get_total_users()
    new_haven_users = set(get_user_within_distance(41.311272, -72.932041, 20, datetime(2015, 2, 1), datetime(2014, 9, 1)))
    users_in_new_markets = all_users - new_haven_users
    users_in_new_markets_qs = User.objects.filter(pk__in=[x.pk for x in users_in_new_markets], date_joined__gte=datetime(2015, 1, 1)).order_by('date_joined')
    return users_in_new_markets_qs


def get_deals_set_within_distance(lat, lng, min_date=datetime.now()-timedelta(weeks=4), max_date=datetime.now()):
    venues = get_venues_within_distance(lat, lng, large_radius)
    deals = Deal.objects.filter(place__in=venues)
    unique_deal_statuses = DealStatus.objects.filter(deal__in=deals, date_created__gte=min_date, contact=None, date_created__lte=max_date).distinct("beacon")
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

def users_in_each_market():
    new_haven_users = get_user_within_distance(41.311272, -72.932041, 2)
    print "New Haven: " + str(len(new_haven_users))
    chapel_hill_users = get_user_within_distance(35.920959, -79.0392909, 20)
    print "Chapel Hill: " + str(len(chapel_hill_users))
    charlottesville_users = get_user_within_distance(38.0400874, -78.4849739, 20)
    print "Charlottesville: " + str(len(charlottesville_users))
    seattle_users = get_user_within_distance(47.667759, -122.312766, 20)
    print "Seattle: " + str(len(seattle_users))
    baton_rouge_users = get_user_within_distance(30.44177, -91.1353653, 20)
    print "Baton Rouge: " + str(len(baton_rouge_users))
    columbus_users = get_user_within_distance(39.993828, -83.006534, 20)
    print "Columbus: " + str(len(columbus_users))
    knoxville_users = get_user_within_distance(35.954401, -83.929456, 20)
    print "Knoxville: " + str(len(knoxville_users))
    chicago_users = get_user_within_distance(42.0042848, -87.6614784, 20)
    print "Chicago: " + str(len(chicago_users))
    quinnipiac_users = get_user_within_distance(41.4194522, -72.8972934, 2)
    print "Quinnipiac: " + str(len(quinnipiac_users))


def get_venue_csv_for_sales(lat, lon, radius):
    bar_parameters = {}
    bar_parameters['radius'] = radius
    bar_parameters['ll'] = "{0},{1}".format(lat, lon)
    bar_parameters['limit'] = 50
    bar_parameters['categoryId']= '4d4b7105d754a06376d81259'
    results = FoursquareClient.shared_client.venues.search(bar_parameters)
    bars = results['venues']

    sorted_list_of_bars = sorted(bars, key=lambda k: k['stats']['checkinsCount'], reverse=True)

    parameters = {}
    parameters['radius'] = radius
    parameters['ll'] = "{0},{1}".format(lat, lon)
    parameters['limit'] = 50
    parameters['categoryId'] = '4d4b7105d754a06374d81259,4bf58dd8d48988d1e0931735'
    results = FoursquareClient.shared_client.venues.search(parameters)
    other_venues = results['venues']
    filtered_other_venues = [item for item in other_venues if item not in bars]

    sorted_list_of_everything_else = sorted(filtered_other_venues, key=lambda k: k['stats']['checkinsCount'], reverse=True)

    return sorted_list_of_bars, sorted_list_of_everything_else

def get_venue_foursquareid(lat, lon, name):
    venue_parameters = {}
    venue_parameters['radius'] = 10
    venue_parameters['ll'] = "{0},{1}".format(lat, lon)
    venue_parameters['query'] = name
    results = FoursquareClient.shared_client.venues.search(venue_parameters)
    if results['venues']:
        return results['venues'][0]['id']
    else:
        return None

def foursquareid_getter():
    for DealPlaceObject in DealPlace.objects.all():
        DealPlaceObject.foursquare_id = get_venue_foursquareid(DealPlaceObject.latitude, DealPlaceObject.longitude, DealPlaceObject.name)
        DealPlaceObject.save()

def foursquare_description_updater():
    for DealPlaceObject in DealPlace.objects.all():
        if DealPlaceObject.foursquare_id:
            if 'description' in FoursquareClient.shared_client.venues(DealPlaceObject.foursquare_id)['venue']:
                description = FoursquareClient.shared_client.venues(DealPlaceObject.foursquare_id)['venue']['description']
                DealPlaceObject.place_description = description
                DealPlaceObject.save()
            else:
                DealPlaceObject.place_description = ""
                DealPlaceObject.save()
        else:
            DealPlaceObject.place_description = ""
            DealPlaceObject.save()

def get_venue_fbid(token):
    graph = facebook.GraphAPI(token)
    for DPO in DealPlace.objects.all():
        search = graph.request('search', args={'q': DPO.name + ' seattle', 'type': 'page'})
        for potvenue in search['data']:
            fbvenue = graph.get_object(id=potvenue['id'])
            if fbvenue['location']['latitude'] < DPO.latitude + 0.01 and fbvenue['location']['latitude'] > DPO.latitude - 0.01 and fbvenue['location']['longitude'] < DPO.longitude + 0.01 and fbvenue['location']['longitude'] > DPO.longitude - 0.01:
                DPO.facebook_id = potvenue['id']
                DPO.save()
                break


def venue_performance(min_date, max_date):
    venues = {}
    deal_statuses = DealStatus.objects.filter(date_created__gte=min_date, date_created__lte=max_date, deal_status=DEAL_STATUS.REDEEMED).exclude(user__in=excluded_users)
    for deal_status in deal_statuses:
        deal_id = deal_status.deal_id
        if deal_id in venues.keys():
            venues[deal_id] += 1
        else:
            venues[deal_id] = 1
    venue_performance_list = []
    for venue_key in venues.keys():
        venue_obj = {}
        deal = Deal.objects.get(pk=venue_key)
        venue_obj['name'] = deal.place.name
        venue_obj['number_of_redemptions'] = venues[venue_key]
        venue_obj['total_cost'] = deal.item_cost * venues[venue_key]
        venue_performance_list.append(venue_obj)
    return venue_performance_list

def daily_digest_sender(fbtoken):
    twitter_consumer_key = "wUXOZqc6WFJIJwDvgkHImdvwC"
    twitter_consumer_secret = "3aQOHvanYUanjmacoXpGvK5SpbxjhENe90QcfVXQ1mHtII4fWY"
    twitter_access_token = "1902770462-UHFJQqfetRqfW2pDfJSEj0LPOOaSWaQLRJqtFzu"
    twitter_access_token_secret = "MnNkzmdUkQuXRppV9jbMCrCIt7fAGSY8GRojWoioCVyQs"
    api = twitter.Api(consumer_key=twitter_consumer_key, consumer_secret=twitter_consumer_secret, access_token_key=twitter_access_token, access_token_secret=twitter_access_token_secret)
    graph = facebook.GraphAPI(fbtoken)
    venues = [{'fbid': 'rheinhausseattle', 'venue': 'Rhein Haus', 'twitterid': 'SeaRheinHaus'}, {'fbid': 'somerandombar', 'venue': 'Some Random Bar'}, {'fbid': '257298464326564', 'venue': 'The Innkeeper'}, {'fbid': 'FremontAbbey', 'venue': 'The Fremont Abbey', 'twitterid': 'fremontabbey'}, {'fbid': 'RooseveltAleHouse', 'venue': 'The Roosevelt Ale House', 'twitterid': 'ralehouse'}, {'fbid': 'vifseattle', 'venue': 'Vif', 'twitterid': 'vifseattle'}, {'venue': 'Herkamer Coffee'}, {'fbid': '116575481734791', 'venue': "Chuck's Hop Shop", 'twitterid': 'Chucks85th'}, {'fbid': 'PecadoBueno', 'venue': 'Pecado Bueno'}, {'venue': "Earl's"}, {'fbid': '91213692268', 'venue': "Finn MacCool's", 'twitterid': 'FinnMacCoolsPub'}, {'fbid': 'CapitolCider', 'venue': 'Capitol Cider', 'twitterid': 'capitolcider'}, {'fbid': 'UnicornSeattle', 'venue': 'Unicorn', 'twitterid': 'unicornseattle'}, {'fbid': 'cha.seattle', 'venue': 'Cha Cha Lounge'}, {'venue': "Lydia's"}, {'fbid': '1421639188112350', 'venue': 'The Maple Bar'}, {'fbid': '194721543893132', 'venue': 'The Little Red Hen', 'twitterid': 'LRHSeattle'}, {'fbid': '143442979052669', 'venue': 'Black Bottle'}, {'fbid': 'BarrioMexicanRestaurant', 'venue': 'Barrio', 'twitterid': 'HeavyRestaurant'}, {'venue': 'Whiskey Bar', 'twitterid': 'thewhiskybarsea'}, {'fbid': 'baroloseattle', 'venue': 'Barolo'}, {'fbid': 'VivaPoquitos', 'venue': 'Poquitos', 'twitterid': 'vivapoquitos'}, {'fbid': 'LloydMartinSeattle', 'venue': 'Lloyd Martin', 'twitterid': 'lloydmartin_qa'}, {'venue': 'List'}, {'fbid': '120226377994905', 'venue': "Sully's Snowgoose Saloon"}, {'fbid': '170451193288', 'venue': 'Cicchetti', 'twitterid': 'Cicchetti_121'}, {'fbid': 'EastlakeZooTavern', 'venue': 'Zoo Tavern', 'twitterid': 'eastlakezoo'}, {'fbid': 'momijiseattle', 'venue': 'Momiji', 'twitterid': 'MomijiSeattle'}, {'fbid': 'TavernLaw', 'venue': 'Tavern Law', 'twitterid': 'mccrackentough'}, {'fbid': '121146961248930', 'venue': 'Prost'}, {'fbid': '210002342362954', 'venue': "Leny's Place"}, {'fbid': 'The.Park.Pub', 'venue': 'Park Pub'}, {'venue': 'Naked City Brewing', 'twitterid': 'nakedcitybeer'}, {'fbid': '226433390713207', 'venue': 'Shelter Lounge'}, {'fbid': 'KingsHardware', 'venue': "King's Hardware", 'twitterid': 'kingsballard'}, {'fbid': '181849332562', 'venue': 'Kangaroo and Kiwi'}, {'fbid': 'ChupacabraGreenwood', 'venue': 'El Chupacabra'}, {'fbid': 'GrimSeattle', 'venue': "Grim's", 'twitterid': 'grimseattle'}, {'fbid': 'libertybar', 'venue': 'Liberty', 'twitterid': 'libertylovesyou'}, {'venue': "Collin's Pub", 'twitterid': 'collinspub'}, {'fbid': '107239092640996', 'venue': 'The Diller Room', 'twitterid': 'TheDillerRoom'}, {'fbid': 'Lecosho', 'venue': 'Lecosho', 'twitterid': 'lecosho'}, {'fbid': 'MetGrill', 'venue': 'Metropolitan Grill', 'twitterid': 'MetGrill'}, {'fbid': 'FrolikSeattle', 'venue': 'Frolik', 'twitterid': 'FrolikSeattle'}, {'venue': 'Rob Roy', 'twitterid': 'RobRoySeattle'}, {'venue': 'White Horse Trading Co.'}, {'fbid': 'angrybeaverseattle', 'venue': 'The Angry Beaver', 'twitterid': 'angrybeaverbar'}, {'fbid': 'essexbar', 'venue': 'Essex'}, {'fbid': 'milsteadandco', 'venue': 'Milstead & Co.', 'twitterid': 'MilsteadandCo'}, {'fbid': 'Local360Seattle', 'venue': 'Local 360', 'twitterid': 'Local360Seattle'}, {'fbid': 'SeattleRoomSeattle', 'venue': 'The Sitting Room'}, {'fbid': 'TheGeraldSeattle', 'venue': 'The Gerald'}, {'fbid': 'CanonSeattle', 'venue': 'Canon', 'twitterid': 'CanonSeattle'}, {'fbid': 'TheSaintSocial', 'venue': 'The Saint', 'twitterid': 'thesaintsocial'}, {'fbid': 'RockBoxSeattle', 'venue': 'Rockbox', 'twitterid': 'RockBoxSeattle'}, {'fbid': 'revelseattle', 'venue': 'Revel', 'twitterid': 'revelseattle'}, {'fbid': '128777587151652', 'venue': 'Fremont Brewing', 'twitterid': 'fremontbrewing'}, {'fbid': 'CanterburyAleHouse', 'venue': 'Canterbury Ale House', 'twitterid': 'thecanterburywa'}, {'fbid': 'WitnessBar', 'venue': 'Witness', 'twitterid': 'TheWitnessBar'}, {'fbid': '362561033827156', 'venue': 'Hillside'}, {'fbid': 'coastal.kitchen.seattle', 'venue': 'Coastal Kitchen', 'twitterid': 'coastalkitchen'}, {'fbid': 'CometSeattle', 'venue': 'Comet Tavern'}, {'venue': 'Elysian Brewery', 'twitterid': 'elysianbrewing'}, {'fbid': '116501908374109', 'venue': 'Cafe Presse'}, {'venue': "Linda's Tavern", 'twitterid': 'lindastavern'}, {'fbid': 'vitosseattle', 'venue': "Vito's", 'twitterid': 'vitosseattle'}, {'venue': 'Galvanize'}, {'fbid': 'OskarsKitchen', 'venue': "Oskar's", 'twitterid': 'oskarsqueenanne'}, {'fbid': 'Rachels.Ginger.Beer', 'venue': "Rachel's Ginger Beer", 'twitterid': 'rgbsoda'}, {'venue': 'Gasworks Park'}, {'fbid': '104506439589308', 'venue': 'Discovery Park'}, {'fbid': 'SeattleCenter', 'venue': 'Seattle Center', 'twitterid': 'seattlecenter'}, {'venue': 'Volunteer Park'}, {'fbid': 'TheChieftainSeattle', 'venue': 'Chieftain'}, {'fbid': 'LostLakeCafe', 'venue': 'Lost Lake'}, {'fbid': 'garagebilliards', 'venue': 'Garage', 'twitterid': 'garagebilliards'}, {'fbid': '160896570641953', 'venue': 'Artusi', 'twitterid': 'ArtusiBar'}, {'fbid': 'Smithseattle', 'venue': 'Smith', 'twitterid': 'Smithseattle'}, {'fbid': '299233916777600', 'venue': 'Pine Box', 'twitterid': 'pinebox'}, {'fbid': '390698354317676', 'venue': 'Hopvine', 'twitterid': 'hopvinepub'}, {'fbid': '160900270643825', 'venue': 'Rabbit Hole'}, {'fbid': '10150110088105200', 'venue': 'Bathtub Gin Co.'}, {'fbid': 'TacosChukis', 'venue': 'Tacos Chukis', 'twitterid': 'tacoschukis'}, {'fbid': 'bardelcorsoseattle', 'venue': 'Bar del Corso', 'twitterid': 'bardelcorso'}, {'fbid': 'captainblacks', 'venue': 'Captain Blacks', 'twitterid': 'captainblacks'}, {'fbid': '116466008380929', 'venue': 'Stumbling Monk', 'twitterid': 'StumblingMonk'}, {'fbid': 'thewaterwheellounge', 'venue': 'Waterwheel Lounge', 'twitterid': 'TheWaterwheel'}, {'venue': "Zayda Buddy's Pizza & Bar", 'twitterid': 'zaydabuddys'}, {'fbid': '185634814800708', 'venue': 'Two Beers Brewing Co.', 'twitterid': 'twobeersbrewing'}, {'fbid': 'percys.seattle', 'venue': "Percy's and Co."}, {'fbid': 'BitterrootSeattle', 'venue': 'Bitterroot', 'twitterid': 'bitterrootbbq'}, {'fbid': 'sextonballard', 'venue': 'The Sexton', 'twitterid': 'sextonseattle'}, {'fbid': '121388547875079', 'venue': 'Delancey', 'twitterid': 'delanceyseattle'}, {'fbid': 'fogonseattle', 'venue': 'Fogon'}, {'fbid': 'LaredosGrill', 'venue': 'Laredos', 'twitterid': 'laredosseattle'}, {'fbid': 'westwardseattle', 'venue': 'Westward'}, {'fbid': '116799065570', 'venue': "Quinn's", 'twitterid': 'quinnsseattle'}, {'fbid': 'babarseattle', 'venue': 'Ba Bar', 'twitterid': 'babarseattle'}, {'fbid': '104508606246040', 'venue': 'Golden Gardens Park'}, {'fbid': '528634177217230', 'venue': 'Alibi Room'}, {'fbid': 'TheBottleNeckLounge', 'venue': 'The Bottle Neck Lounge', 'twitterid': 'bneck'}, {'fbid': '155509047801321', 'venue': 'Red Door', 'twitterid': 'reddoorseattle'}, {'fbid': 'BleuBistroGrotto', 'venue': 'Bleu Bistro Grotto', 'twitterid': 'bleugrotto'}, {'fbid': 'STOUTseattle', 'venue': 'STOUT', 'twitterid': 'stoutseattle'}, {'fbid': 'TheNabobBar', 'venue': 'The Great Nabob', 'twitterid': 'thenabobbar'}, {'fbid': '548939168555983', 'venue': 'Radiator Whiskey', 'twitterid': 'radiatorwhiskey'}, {'fbid': '214772361881001', 'venue': 'Ballroom', 'twitterid': 'ballroomseattle'}, {'fbid': 'belltownpub', 'venue': 'Belltown Pub', 'twitterid': 'thebelltownpub'}, {'fbid': '127965500586156', 'venue': 'Cafe Solstice', 'twitterid': 'cafesolsticesea'}, {'fbid': 'garagebilliards', 'venue': 'Garage', 'twitterid': 'garagebilliards'}, {'fbid': 'BuckleysQueenAnne', 'venue': "Buckley's"}]
    users = [{'email': 'jazjit.singh@gmail.com', 'favorites': ['Unicorn', 'Rhein Haus', 'Chieftain', 'Lost Lake', 'Cha Cha Lounge', 'Garage']}, {'email': 'kcjonson@gmail.com', 'favorites': ['Artusi', 'Smith', "Linda's Tavern", 'Pine Box', 'Cantebury', 'Hopvine', 'Rabbit Hole', 'Bathtub Gin']}, {'email': 'crawford.89@gmail.com', 'favorites': ['The Fremont Abbey', 'The Roosevelt Ale House', 'Essex', 'Lost Lake', 'Hopvine', 'Waterwheel Lounge', "Zayda Buddy's Pizza & Bar", 'Two Beers Brewing Co.', "Percy's and Co.", 'Bitterroot', 'The Sexton']}, {'email': 'austin.n.walters@gmail.com', 'favorites': ['Revel', 'Bar del Corso', 'Delancey', 'Fogon', 'Laredos', 'Westward', "Quinn's"]}, {'email': 'Josh.maslin@gmail.com', 'favorites': ['Barrio', 'Gasworks Park', 'Ba Bar', 'Golden Gardens Park']}, {'email': 'adam.s.kowalke@gmail.com', 'favorites': ['The Diller Room', 'White Horse Trading Co.', 'Alibi Room', 'The Bottle Neck Lounge']}, {'email': 'sdesmond46@gmail.com', 'favorites': ['Canterbury Ale House', 'Red Door', 'Bleu Bistro Grotto', 'STOUT']}, {'email': 'hajpoj@gmail.com', 'favorites': ['Rhein Haus']}, {'email': 'Mcamila_saad@gmail.com', 'favorites': ['Some Random Bar', 'The Innkeeper']}, {'email': 'Andrewpatrickzook@gmail.com', 'favorites': ['The Fremont Abbey', 'The Roosevelt Ale House', 'Vif', 'Herkamer Coffee', "Chuck's Hop Shop", 'Pecado Bueno']}, {'email': 'kathrynguess@gmail.com', 'favorites': ['Cha Cha Lounge', "Lydia's"]}, {'email': 'felicitywood@gmail.com', 'favorites': ['The Innkeeper', 'The Roosevelt Ale House', 'The Maple Bar', 'The Little Red Hen', 'Black Bottle', 'Barrio', 'Whiskey Bar', 'Barolo', 'Poquitos', 'Lloyd Martin']}, {'email': 'mail@mattgoyer.com', 'favorites': ['Unicorn', 'Barrio', "Sully's Snowgoose Saloon", 'Cicchetti', 'Zoo Tavern', 'Momiji', 'Tavern Law']}, {'email': 'zoecolleen@gmail.com', 'favorites': ["Chuck's Hop Shop", 'The Little Red Hen', 'Prost', "Leny's Place", 'Park Pub', 'Naked City Brewing', 'Shelter Lounge', "King's Hardware", 'Kangaroo and Kiwi', 'El Chupacabra']}, {'email': 'sibjeet@gmail.com', 'favorites': ["Chuck's Hop Shop", 'Capitol Cider', 'Unicorn', "Grim's", 'Liberty']}, {'email': 'rlucas@rlucas.net', 'favorites': ["Collin's Pub", 'The Diller Room', 'Lecosho', 'Metropolitan Grill', 'Frolik', 'Rob Roy', 'White Horse Trading Co.']}, {'email': 'Aaronjosephdavidson@gmail.com', 'favorites': ['The Roosevelt Ale House', "King's Hardware", 'The Angry Beaver', 'Milstead & Co.', 'Essex']}, {'email': 'bcstoutbackup@gmail.com', 'favorites': ['Some Random Bar', 'Local 360', 'The Sitting Room']}, {'email': 'info@dellachen.com', 'favorites': ['Essex', 'The Gerald', 'Canon', 'The Saint']}, {'email': 'taylorlm86@gmail.com', 'favorites': ['Canon', 'Rockbox', 'Revel', 'Fremont Brewing']}, {'email': 'ejayres@gmail.com', 'favorites': ['Fremont Brewing', 'Canterbury Ale House', 'Witness', 'Hillside']}, {'email': 'rhettdb2005@gmail.com', 'favorites': ['Coastal Kitchen', 'Elysian Brewery', 'Volunteer Park', 'The Great Nabob']}, {'email': 'beccasamuelson@gmail.com', 'favorites': ['Capitol Cider', 'Galvanize', "Oskar's", "Rachel's Ginger Beer", 'Gasworks Park', 'Discovery Park', 'Seattle Center']}, {'email': 'tiffanychen.la@gmail.com', 'favorites': ['Poquitos', 'Tavern Law', 'Canon', 'Comet Tavern', 'Cafe Presse', "Linda's Tavern", "Vito's"]}, {'email': 'nofmxc@gmail.com', 'favorites': ['Rhein Haus', 'Unicorn', 'Canterbury Ale House', 'Garage', 'Captain Blacks', 'Stumbling Monk']}, {'email': 'brendanr@gmail.com', 'favorites': ["Linda's Tavern", 'Tacos Chukis', 'Bar del Corso']}, {'email': 'Jaredfoxjones@gmail.com', 'favorites': ['Rob Roy', 'Radiator Whiskey', 'Laredos', 'Ballroom', 'Belltown Pub', 'Rhein Haus', 'Cafe Solstice', 'Black Bottle', 'Cha Cha Lounge']}, {'email': 'annejones817@gmail.com', 'favorites': ['Rhein Haus', 'Belltown Pub', 'Garage', "Buckley's"]}]
    for user in users:
        now = datetime.now()
        body = ""
        points = 0
        for favorite in user['favorites']:
            samepost = False
            facebookposts = []
            socialfeed = ""
            events = ""
            venuefbid = None
            venuetwitterid = None
            for venue in venues:
                if venue['venue'] == favorite:
                    if 'fbid' in venue.keys():
                        venuefbid = venue['fbid']
                    if 'twitterid' in venue.keys():
                        venuetwitterid = venue['twitterid']
                    break
            if venuefbid:
                try:
                    posts = graph.get_object(id=venuefbid + "/posts")
                except:
                    continue
                for x in range(0, min(5, len(posts['data']))):
                    timestamp = posts['data'][x]['created_time']
                    DTtimestamp = datetime.strptime(timestamp,'%Y-%m-%dT%H:%M:%S+0000')
                    if DTtimestamp > now - timedelta(hours=23):
                        posttype = posts['data'][x]['type']
                        if posttype == 'photo':
                            points = points + 1
                            if 'message' in posts['data'][x].keys():
                                socialfeed = socialfeed + """<tr> <td style="padding-left:75px; padding-right:100px; text-align:left"> <span style="font-size:14px; font-family:Helvetica Neue,Helvetica,Arial,sans-serif"><strong>Facebook: </strong></span> <span style="font-size:12px; font-family:Helvetica Neue,Helvetica,Arial,sans-serif">""" + posts['data'][x]['message'].replace("\n", "<br>") + """</span><br></td></tr><tr width="100%"> <td width="100%" align="center"> <img style="max-width:300px;" src='""" + graph.get_object(id=posts['data'][x]['object_id'])['source'] + """'> </td></tr>"""
                                facebookposts.append(posts['data'][x]['message'])
                            else:
                                socialfeed = socialfeed + """<tr> <td style="padding-left:75px; padding-right:100px; text-align:left"> <span style="font-size:14px; font-family:Helvetica Neue,Helvetica,Arial,sans-serif"><strong>Facebook: </strong></span> <span style="font-size:12px; font-family:Helvetica Neue,Helvetica,Arial,sans-serif"></span><br></td></tr><tr width="100%"> <td width="100%" align="center"> <img style="max-width:300px;" src='""" + graph.get_object(id=posts['data'][x]['object_id'])['source'] + """'> </td></tr>"""

                        elif posttype == 'status':
                            points = points + 1
                            facebookposts.append(posts['data'][x]['message'])
                            socialfeed = socialfeed + """<tr> <td style="padding-left:75px; padding-right:100px; text-align:left"> <span style="font-size:14px; font-family:Helvetica Neue,Helvetica,Arial,sans-serif"><strong>Facebook: </strong></span> <span style="font-size:12px; font-family:Helvetica Neue,Helvetica,Arial,sans-serif">""" + posts['data'][x]['message'].replace("\n", "<br>") + """</span><br></td></tr>"""
                        elif posttype == 'event':
                            points = points + 2
                            facebookposts.append(posts['data'][x]['description'])
                            events = events + """<tr> <td style="padding-left:75px; padding-right:100px; text-align:left"> <span style="font-size:14px; font-family:Helvetica Neue,Helvetica,Arial,sans-serif"><strong>""" + posts['data'][x]['name'] + """ </strong></span> <span style="font-size:12px; font-family:Helvetica Neue,Helvetica,Arial,sans-serif">""" + posts['data'][x]['description'].replace("\n", "<br>") + "<br><br>Link: " + posts['data'][x]['link'] + """</span><br></td></tr>"""
                        elif posttype == 'link':
                            points = points + 1
                            facebookposts.append(posts['data'][x]['message'])
                            socialfeed = socialfeed + """<tr> <td style="padding-left:75px; padding-right:100px; text-align:left"> <span style="font-size:14px; font-family:Helvetica Neue,Helvetica,Arial,sans-serif"><strong>Facebook: </strong></span> <span style="font-size:12px; font-family:Helvetica Neue,Helvetica,Arial,sans-serif">""" + posts['data'][x]['message'].replace("\n", "<br>") + "<br>Link: " + posts['data'][x]['link'] + """</span><br></td></tr>"""
                    else:
                        break
            if venuetwitterid:
                statuses = api.GetUserTimeline(screen_name=venuetwitterid, include_rts=False, exclude_replies=True)
                for x in range(0, min(5, len(statuses))):
                    timestamp = statuses[x].created_at
                    DTtimestamp = datetime.strptime(timestamp, '%a %b %d %H:%M:%S +0000 %Y')
                    if DTtimestamp > now - timedelta(hours=20):
                        for facebookpost in facebookposts:
                            if fuzz.token_set_ratio(statuses[x].text, facebookpost) > 60:
                                print statuses[x].text
                                print facebookpost
                                samepost = True
                        if samepost == False:
                            points = points + 1
                            if statuses[x].media:
                                if statuses[x].media[0]['type'] == 'photo':
                                    trblock = """<tr> <td style="padding-left:75px; padding-right:100px; text-align:left"> <span style="font-size:14px; font-family:Helvetica Neue,Helvetica,Arial,sans-serif"><strong>Twitter: </strong></span> <span style="font-size:12px; font-family:Helvetica Neue,Helvetica,Arial,sans-serif">{{Message}}</span><br></td></tr><tr width="100%"> <td width="100%" align="center"> <img style="max-width:300px;" src='{{Picture Source}}'> </td></tr>"""
                                    trblock = trblock.replace("{{Picture Source}}", statuses[x].media[0]['media_url_https'])
                                    trblock = trblock.replace("{{Message}}", statuses[x].text.replace("\n", "<br>"))
                                    socialfeed = socialfeed + trblock
                            else:
                                trblock = """<tr> <td style="padding-left:75px; padding-right:100px; text-align:left"> <span style="font-size:14px; font-family:Helvetica Neue,Helvetica,Arial,sans-serif"><strong>Twitter: </strong></span> <span style="font-size:12px; font-family:Helvetica Neue,Helvetica,Arial,sans-serif">{{Message}}</span><br></td></tr>"""
                                trblock = trblock.replace("{{Message}}", statuses[x].text.replace("\n", "<br>"))
                                socialfeed = socialfeed + trblock
                        else:
                            samepost = False
                    else:
                        break
            if events and socialfeed:
                body = body + """<table width="100%"> <tr width="100%"> <td width="100%" align="center"> <span style="font-size:23px; font-family:Helvetica Neue,Helvetica,Arial,sans-serif"><strong>""" + favorite.upper() + """</strong></span> </td></tr><tr> <td style="padding-left:50px;"> <span style="font-size:15px; font-family:Helvetica Neue,Helvetica,Arial,sans-serif">EVENTS AND SPECIALS:</span> </td></tr>""" + events + """<br><br><tr> <td style="padding-left:50px;"> <span style="font-size:15px; font-family:Helvetica Neue,Helvetica,Arial,sans-serif">SOCIAL FEED:</span> </td></tr>""" + socialfeed + """</table>"""
            elif events:
                body = body + """<table width="100%"> <tr width="100%"> <td width="100%" align="center"> <span style="font-size:23px; font-family:Helvetica Neue,Helvetica,Arial,sans-serif"><strong>""" + favorite.upper() + """</strong></span> </td></tr><tr> <td style="padding-left:50px;"> <span style="font-size:15px; font-family:Helvetica Neue,Helvetica,Arial,sans-serif">EVENTS AND SPECIALS:</span> </td></tr>""" + events + """</table>"""
            elif socialfeed:
                body = body + """<table width="100%"> <tr width="100%"> <td width="100%" align="center"> <span style="font-size:23px; font-family:Helvetica Neue,Helvetica,Arial,sans-serif"><strong>""" + favorite.upper() + """</strong></span> </td></tr><tr> <td style="padding-left:50px;"> <span style="font-size:15px; font-family:Helvetica Neue,Helvetica,Arial,sans-serif">SOCIAL FEED:</span> </td></tr>""" + socialfeed + """</table>"""
        html = """<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd"><html xmlns="http://www.w3.org/1999/xhtml"><head> <meta http-equiv="Content-Type" content="text/html; charset=utf-8"/> <meta name="viewport" content="width=device-width, initial-scale=1.0"/> <title>Hotspot Welcome</title> <style type="text/css"> /* Based on The MailChimp Reset INLINE: Yes. */ /* Client-specific Styles */ #outlook a{padding: 0;}/* Force Outlook to provide a "view in browser" menu link. */ body{width: 100% !important; -webkit-text-size-adjust: 100%; -ms-text-size-adjust: 100%; margin: 0; padding: 0;}/* Prevent Webkit and Windows Mobile platforms from changing default font sizes.*/ .ExternalClass{width: 100%;}/* Force Hotmail to display emails at full width */ .ExternalClass, .ExternalClass p, .ExternalClass span, .ExternalClass font, .ExternalClass td, .ExternalClass div{line-height: 100%;}/* Forces Hotmail to display normal line spacing. More on that: http://www.emailonacid.com/forum/viewthread/43/ */ #backgroundTable{margin: 0; padding: 0; width: 100% !important; line-height: 150%;}/* End reset */ /* Some sensible defaults for imagesBring inline: Yes. */ img{outline: none; text-decoration: none; -ms-interpolation-mode: bicubic;}a img{border: none;}@import url(http://fonts.googleapis.com/css?family=Lato); /*@font-face{font-family: "HelveticaNeueLight"; src: url(https://s3-us-west-2.amazonaws.com/hotspot-static/static/font/HelveticaNeueLTCom-Lt.ttf) format("truetype");}@font-face{font-family: "HelveticaNeueBold"; src: url(https://s3-us-west-2.amazonaws.com/hotspot-static/static/font/HelveticaNeue-Bold.otf) format("opentype");}*/ /*strong{font-family: "HelveticaNeueBold"; font-weight: 500 !important;}*/ .image_fix{display: block;}/* Yahoo paragraph fixBring inline: Yes. */ p{margin: 1em 0;}span{color: black !important;}/* Hotmail header color resetBring inline: Yes. */ h1, h2, h3, h4, h5, h6{color: black !important;}h1 a, h2 a, h3 a, h4 a, h5 a, h6 a{color: blue !important;}h1 a:active, h2 a:active, h3 a:active, h4 a:active, h5 a:active, h6 a:active{color: red !important; /* Preferably not the same color as the normal header link color. There is limited support for psuedo classes in email clients, this was added just for good measure. */}h1 a:visited, h2 a:visited, h3 a:visited, h4 a:visited, h5 a:visited, h6 a:visited{color: black !important; /* Preferably not the same color as the normal header link color. There is limited support for psuedo classes in email clients, this was added just for good measure. */}/* Outlook 07, 10 Padding issue fixBring inline: No.*/ table td{border-collapse: collapse;}/* Remove spacing around Outlook 07, 10 tablesBring inline: Yes */ table{border-collapse: collapse; mso-table-lspace: 0pt; mso-table-rspace: 0pt;}/* Styling your links has become much simpler with the new Yahoo. In fact, it falls in line with the main credo of styling in email and make sure to bring your styles inline. Your link colors will be uniform across clients when brought inline.Bring inline: Yes. */ a{color: #00a6d5;}/*******************************************************************************************************MOBILE TARGETING*******************************************************************************************************/ @media only screen and (max-device-width: 480px){/* Part one of controlling phone number linking for mobile. */ a[href^="tel"], a[href^="sms"]{text-decoration: none; color: blue; /* or whatever your want */ pointer-events: none; cursor: default;}.mobile_link a[href^="tel"], .mobile_link a[href^="sms"]{text-decoration: default; color: orange !important; pointer-events: auto; cursor: default;}}/* More Specific Targeting */ @media only screen and (min-device-width: 768px) and (max-device-width: 1024px){/* You guessed it, ipad (tablets, smaller screens, etc) */ /* repeating for the ipad */ a[href^="tel"], a[href^="sms"]{text-decoration: none; color: blue; /* or whatever your want */ pointer-events: none; cursor: default;}.mobile_link a[href^="tel"], .mobile_link a[href^="sms"]{text-decoration: default; color: orange !important; pointer-events: auto; cursor: default;}}@media only screen and (-webkit-min-device-pixel-ratio: 2){/* Put your iPhone 4g styles in here */}/* Android targeting */ @media only screen and (-webkit-device-pixel-ratio: .75){/* Put CSS for low density (ldpi) Android layouts in here */}@media only screen and (-webkit-device-pixel-ratio: 1){/* Put CSS for medium density (mdpi) Android layouts in here */}@media only screen and (-webkit-device-pixel-ratio: 1.5){/* Put CSS for high density (hdpi) Android layouts in here */}</style> <head> <meta http-equiv="Content-Type" content="text</html; charset=UTF-8"> </head></head> <body> <div style="margin:0px 0px 0px 0px;padding:0px 0px 0px 0px;font-family: 'Lato';"> <table cellpadding="0" cellspacing="0" border="0" align="center" width="600px"> <tbody> <tr> <td> <br><table width="100%" bgcolor="#ffffff"> <tr height="20px"> <td align="center" valign="top"> <a href="http://www.GetHotspotApp.com" target="_blank"> <img src="https://s3-us-west-2.amazonaws.com/hotspot-venue-images/new_logo.png" alt="Hotspot Logo"> </a> </td></tr><tr height="100%"> <td align="center" valign="top" style="padding-top:15px"> <span color="#000000" style="font-size:25px; font-family:Helvetica Neue,Helvetica,Arial,sans-serif"><strong>TODAY'S NEWS AND EVENTS</strong></span> </td></tr><tr> <td align="center" valign="top" style="padding-top:5px;padding-left:65px;padding-right:65px;padding-bottom:25px;"> <span style="font-size:15px; font-family:Helvetica Neue,Helvetica,Arial,sans-serif">From your favorite hang-out spots in Seattle</span> </td></tr></table>""" + body + """<table width="100%" height="140px" cellpadding="0" cellspacing="0" border="0" style="background:#FFFFFF;"> <tr> <br><td width="43%" border="0" valign="top" style="padding-left:50px; padding-top:25px;"> <div><a valign="top" style="font-size:12px; color:#000000;">&#169;2015 Hotspot, Inc.</a> <br><a style="font-size:12px; color:#00a6d5" href="http://www.gethotspotapp.com/">www.gethotspotapp.com</a> <br><a style="font-size:12px; color:#000000">Reply 'unsubscribe' to unsubscribe</a> </td><td width="57%" align="right" valign="top" style="padding-right:50px; padding-top:25px; text-decoration:none"> <a style="text-decoration:none" href="https://www.facebook.com/hotspotapp" target="_blank"> <img style="padding-left:15px" src="https://s3-us-west-2.amazonaws.com/hotspot-static/img/emailFacebookShare.png" alt="Facebook"> </a> <a style="text-decoration:none" href="https://twitter.com/GetHotspotApp" target="_blank"> <img style="padding-left:15px" src="https://s3-us-west-2.amazonaws.com/hotspot-static/img/emailTwitterShare.png" alt="Twitter"> </a> <a style="text-decoration:none" href="mailto:info@gethotspotapp.com" target="_blank"> <img style="padding-left:15px" src="https://s3-us-west-2.amazonaws.com/hotspot-static/img/emailEmailShare.png" alt="Email"> </a> <a style="text-decoration:none" href="https://hotspotapp.wordpress.com/" target="_blank"> <img style="padding-left:15px" src="https://s3-us-west-2.amazonaws.com/hotspot-static/img/blogEmailShare.png" alt="Blog"> </a> </td></tr></table> </body></html>"""
        if points > 1:
            send_marketing_email("william.xu@gethotspotapp.com", "Will Xu", [user['email']], "Seattle favorite venue digest", " ", html, "digest")
            send_marketing_email("william.xu@gethotspotapp.com", "Will Xu", ["wxu121@gmail.com", "jazjit.singh@gmail.com", "jaredfoxjones@gmail.com"], "Seattle favorite venue digest", " ", html, "digesttest")
            #send_marketing_email("william.xu@gethotspotapp.com", "Will Xu", ["wxu121@gmail.com"], "Seattle favorite venue digest", " ", html, "digesttest")
        print user['email'], points

def host_image(website_link, filename):
    conn = S3Connection('AKIAI6LCAFR7YH2HWDUA', 'WntEe+c+HELEQZcFwS1+Stgq7G1XAPMnwOy2kjCK')
    b = conn.get_bucket('hotspot-static')
    k = Key(b)
    k.key = "/img/" + filename
    urllib.urlretrieve(website_link, "temp.png")
    k.set_contents_from_filename("temp.png")
    url = "https://s3-us-west-2.amazonaws.com/" + b.name + k.key
    print "File hosted at: " + url

def does_filename_exist(filename):
    conn = S3Connection('AKIAI6LCAFR7YH2HWDUA', 'WntEe+c+HELEQZcFwS1+Stgq7G1XAPMnwOy2kjCK')
    b = conn.get_bucket("hotspot-static")
    possible_key = b.get_key("/img/" + filename)
    if possible_key:
        print "File already exists"
        return 1
    else:
        print "File does not exist"
        return 0

def get_promo_install_info(users):
    referral_promo_installs = []
    nonreferral_promo_installs = []
    for user in users:
        rewards = RewardItem.objects.filter(user=user)
        for each in rewards:
            if each.promo_code:
                promo_obj = Promo.objects.get(promo_code=each.promo_code)
                if promo_obj.referring_user:
                    referral_promo_installs.append(user)
                    break
                else:
                    nonreferral_promo_installs.append(user)
                    break
    return {'referral_promo_installs': referral_promo_installs, 'nonreferral_promo_installs': nonreferral_promo_installs}

def get_download_install_info(profiles, contact_statuses):
    download_invite_installs = []
    download_invite_installs_outside_seattle = []
    download_invite_noninstalls = []
    download_invite_uniques = []
    unique_phone_numbers = []
    for contact_status in contact_statuses:
        if contact_status.contact:
            if contact_status.contact.normalized_phone not in unique_phone_numbers:
                unique_phone_numbers.append(contact_status.contact.normalized_phone)
                download_invite_uniques.append(contact_status)
            if contact_status.installed_app and profiles.filter(normalized_phone=contact_status.contact.normalized_phone).exists():
                download_invite_installs.append(contact_status)
            elif contact_status.installed_app:
                download_invite_installs_outside_seattle.append(contact_status)
            else:
                download_invite_noninstalls.append(contact_status)
    return {'download_invite_installs': download_invite_installs, 'download_invite_installs_outside_seattle': download_invite_installs_outside_seattle, 'download_invite_noninstalls': download_invite_noninstalls, 'download_invite_uniques': download_invite_uniques}

def get_event_install_info(profiles, contact_statuses):
    event_invite_installs = []
    event_invite_installs_outside_seattle = []
    event_invite_noninstalls = []
    event_invite_uniques = []
    unique_phone_numbers = []
    for contact_status in contact_statuses:
        if contact_status.deal_status:
            if contact_status.deal_status.invited_by and contact_status.deal_status.contact:
                if contact_status.deal_status.contact.normalized_phone not in unique_phone_numbers:
                    unique_phone_numbers.append(contact_status.deal_status.contact.normalized_phone)
                    event_invite_uniques.append(contact_status)
                if contact_status.installed_app and profiles.filter(normalized_phone=contact_status.deal_status.contact.normalized_phone).exists():
                    event_invite_installs.append(contact_status)
                elif contact_status.installed_app:
                    event_invite_installs_outside_seattle.append(contact_status)
                else:
                    event_invite_noninstalls.append(contact_status)
            if contact_status.deal_status.user:
                if contact_status.deal_status.user.username not in unique_phone_numbers:
                    unique_phone_numbers.append(contact_status.deal_status.user.username)
                    event_invite_uniques.append(contact_status)
                if contact_status.installed_app and contact_status.deal_status.user.profile in profiles:
                    event_invite_installs.append(contact_status)
                elif contact_status.installed_app:
                    event_invite_installs_outside_seattle.append(contact_status)
                else:
                    event_invite_noninstalls.append(contact_status)
    return {'event_invite_installs': event_invite_installs, 'event_invite_installs_outside_seattle': event_invite_installs_outside_seattle, 'event_invite_noninstalls': event_invite_noninstalls, 'event_invite_uniques': event_invite_uniques}

def get_website_install_info(profiles, contact_statuses):
    website_installs = []
    website_installs_outside_seattle = []
    website_noninstalls = []
    website_uniques = []
    unique_phone_numbers = []
    for contact_status in contact_statuses:
        if contact_status.phone_number:
            if contact_status.phone_number not in unique_phone_numbers:
                unique_phone_numbers.append(contact_status.phone_number)
                website_uniques.append(contact_status)
            if contact_status.installed_app and profiles.filter(normalized_phone=contact_status.phone_number).exists():
                website_installs.append(contact_status)
            elif contact_status.installed_app:
                website_installs_outside_seattle.append(contact_status)
            else:
                website_noninstalls.append(contact_status)
    return {'website_installs': website_installs, 'website_installs_outside_seattle': website_installs_outside_seattle, 'website_noninstalls': website_noninstalls, 'website_uniques': website_uniques}


def get_user_growth_stats(lat=47.667759, lng=-122.312766, distance=20, start_date = datetime.now(), number_of_weeks=6):
    users = get_user_within_distance(lat, lng, distance)
    profiles = Profile.objects.filter(user__in=users)

    for week in range(0, number_of_weeks):
        today = start_date - timedelta(weeks=week)
        last_week = start_date - timedelta(weeks=week + 1)
        total_users_to_date = users.filter(date_joined__lt=today)
        total_users_last_week = users.filter(date_joined__lt=last_week)
        new_users_this_week = users.filter(date_joined__lt=today, date_joined__gt=last_week)
        number_of_new_users_this_week = len(new_users_this_week)
        percentage_increase = len(new_users_this_week)/float(len(total_users_last_week))
        contact_statuses = ContactStatus.objects.filter(date_created__gt=last_week, date_created__lt=today)

        promo_install_info = get_promo_install_info(new_users_this_week)
        number_of_referral_promo_installs = len(promo_install_info['referral_promo_installs'])
        number_of_nonreferral_promo_installs = len(promo_install_info['nonreferral_promo_installs'])

        download_install_info = get_download_install_info(profiles, contact_statuses)
        number_of_download_invite_installs = len(download_install_info['download_invite_installs'])
        number_of_download_invitations_sent = len(download_install_info['download_invite_installs']) + len(download_install_info['download_invite_noninstalls'])
        number_of_download_invitations_sent_to_uniques = len(download_install_info['download_invite_uniques'])
        if number_of_download_invitations_sent != 0:
            ratio_of_download_invitation_uniques_to_nonuniques = number_of_download_invitations_sent_to_uniques / float(number_of_download_invitations_sent)
        else:
            ratio_of_download_invitation_uniques_to_nonuniques = 0
        if number_of_download_invitations_sent_to_uniques != 0:
            download_invite_conversion_rate = number_of_download_invite_installs / float(number_of_download_invitations_sent_to_uniques)
        else:
            download_invite_conversion_rate = 0

        event_install_info = get_event_install_info(profiles, contact_statuses)
        number_of_event_invite_installs = len(event_install_info['event_invite_installs'])
        number_of_event_invitations_sent = len(event_install_info['event_invite_installs']) + len(event_install_info['event_invite_noninstalls'])
        number_of_event_invitations_sent_to_uniques = len(event_install_info['event_invite_uniques'])
        if number_of_event_invitations_sent != 0:
            ratio_of_event_invitation_uniques_to_nonuniques = number_of_event_invitations_sent_to_uniques / float(number_of_event_invitations_sent)
        else:
            ratio_of_event_invitation_uniques_to_nonuniques = 0
        if number_of_event_invitations_sent_to_uniques != 0:
            event_invite_conversion_rate = number_of_event_invite_installs / float(number_of_event_invitations_sent_to_uniques)
        else:
            event_invite_conversion_rate = 0

        website_install_info = get_website_install_info(profiles, contact_statuses)
        number_of_website_installs = len(website_install_info['website_installs'])
        number_of_website_uniques = len(website_install_info['website_uniques'])
        if number_of_website_uniques != 0:
            website_conversion_rate = number_of_website_installs / float(number_of_website_uniques)
        else:
            website_conversion_rate = 0

        number_of_organic_installs = number_of_new_users_this_week - number_of_nonreferral_promo_installs - number_of_referral_promo_installs - number_of_download_invite_installs - number_of_event_invite_installs - number_of_website_installs

        print "Week: " + str(number_of_weeks - week)
        print "Total Users: " + str(len(total_users_to_date))
        print "New Users: " + str(number_of_new_users_this_week)
        print "    Organic Installs: " + str(number_of_organic_installs)
        print "    Non-referral Promo Installs: " + str(number_of_nonreferral_promo_installs)
        print ""
        print "    Website Installs: " + str(number_of_website_installs)
        print "        Unique Phone Numbers Entered Into Website: " + str(number_of_website_uniques)
        print "        Website Conversion Rate: " + str(round(website_conversion_rate * 100, 2)) + "%"
        print ""
        print "    Referral Installs: " + str(number_of_referral_promo_installs + number_of_download_invite_installs + number_of_event_invite_installs)
        print ""
        print "        Installs from Download Referrals: " + str(number_of_download_invite_installs)
        print "        Installs from Event Referrals: " + str(number_of_event_invite_installs)
        print "        Installs from Promo Referrals: " + str(number_of_referral_promo_installs)
        print "        Total Unique Download Invites Sent: " + str(number_of_download_invitations_sent_to_uniques)
        print "        Total Unique Event Invites Sent (to non-users): " + str(number_of_event_invitations_sent_to_uniques)
        print "        Download Referrals Conversion Rate: " + str(round(download_invite_conversion_rate * 100, 2)) + "%"
        print "        Event Referrals Conversion Rate: " + str(round(event_invite_conversion_rate * 100, 2)) + "%"
        print ""
        print "Total User Percentage Increase: " + str(round(percentage_increase * 100, 2)) + "%"
        print "    Percentage Increase from Organic: " + str(round((number_of_organic_installs / float(number_of_new_users_this_week)) * 100, 2)) + "%"
        print "    Percentage Increase from Non-referral Promo: " + str(round((number_of_nonreferral_promo_installs / float(number_of_new_users_this_week)) * 100, 2)) + "%"
        print "    Percentage Increase from Website: " + str(round((number_of_website_installs / float(number_of_new_users_this_week)) * 100, 2)) + "%"
        print "    Percentage Increase from Download Invite: " + str(round((number_of_download_invite_installs / float(number_of_new_users_this_week)) * 100, 2)) + "%"
        print "    Percentage Increase from Event Invite: " + str(round((number_of_event_invite_installs / float(number_of_new_users_this_week)) * 100, 2)) + "%"
        print "    Percentage Increase from Referral Promo: " + str(round((number_of_referral_promo_installs / float(number_of_new_users_this_week)) * 100, 2)) + "%"
        print ""
        print "--------------------------------------------"
        print ""

    end_date = start_date - timedelta(weeks=number_of_weeks)
    total_contact_statuses = ContactStatus.objects.filter(date_created__lt=start_date, date_created__gt=end_date)
    new_users_over_this_period = users.filter(date_joined__lt=start_date, date_joined__gt=end_date)
    number_of_new_users_over_this_period = len(new_users_over_this_period)
    total_number_of_users_before = len(users.filter(date_joined__lt=end_date))
    total_percentage_increase = number_of_new_users_over_this_period / float(total_number_of_users_before)

    total_promo_install_info = get_promo_install_info(new_users_over_this_period)
    total_referral_promo_installs = len(total_promo_install_info['referral_promo_installs'])
    total_nonreferral_promo_installs = len(total_promo_install_info['nonreferral_promo_installs'])

    total_download_install_info = get_download_install_info(profiles, total_contact_statuses)
    total_download_invite_installs = len(total_download_install_info['download_invite_installs'])
    #total_download_invite_noninstalls = len(total_download_install_info['download_invite_noninstalls'])
    total_download_invite_uniques = len(total_download_install_info['download_invite_uniques'])
    if total_download_invite_uniques != 0:
        total_download_invite_conversion_rate = total_download_invite_installs / float(total_download_invite_uniques)
    else:
        total_download_invite_conversion_rate = 0

    total_event_install_info = get_event_install_info(profiles, total_contact_statuses)
    total_event_invite_installs = len(total_event_install_info['event_invite_installs'])
    total_event_invite_uniques = len(total_event_install_info['event_invite_uniques'])
    if total_event_invite_uniques != 0:
        total_event_invite_conversion_rate = total_event_invite_installs / float(total_event_invite_uniques)
    else:
        total_event_invite_conversion_rate = 0

    total_website_install_info = get_website_install_info(profiles, total_contact_statuses)
    total_website_installs = len(total_website_install_info['website_installs'])
    total_website_uniques = len(total_website_install_info['website_uniques'])
    if total_website_uniques != 0:
        total_website_conversion_rate = total_website_installs / float(total_website_uniques)
    else:
        total_website_conversion_rate = 0

    total_organic_installs = number_of_new_users_over_this_period - total_referral_promo_installs - total_nonreferral_promo_installs - total_download_invite_installs - total_event_invite_installs - total_website_installs

    print "6 Week Averages:"
    print "    New Users: " + str(number_of_new_users_over_this_period)
    print "        Organic Installs: " + str(total_organic_installs)
    print "        Non-referral Promo Installs: " + str(total_nonreferral_promo_installs)
    print ""
    print "        Website Installs: " + str(total_website_installs)
    print "            Unique Phone Numbers Entered Into Website: " + str(total_website_uniques)
    print "            Website Conversion Rate: " + str(round(total_website_conversion_rate * 100, 2)) + "%"
    print ""
    print "        Referral Installs: " + str(total_referral_promo_installs + total_download_invite_installs + total_event_invite_installs)
    print ""
    print "            Installs from Download Referrals: " + str(total_download_invite_installs)
    print "            Installs from Event Referrals: " + str(total_event_invite_installs)
    print "            Installs from Promo Referrals: " + str(total_referral_promo_installs)
    print "            Total Unique Download Invites Sent: " + str(total_download_invite_uniques)
    print "            Total Unique Event Invites Sent (to non-users): " + str(total_event_invite_uniques)
    print "            Download Referrals Conversion Rate: " + str(round(total_download_invite_conversion_rate * 100, 2)) + "%"
    print "            Event Referrals Conversion Rate: " + str(round(total_event_invite_conversion_rate * 100, 2)) + "%"
    print ""
    print "    Total User Percentage Increase: " + str(round(total_percentage_increase * 100, 2)) + "%"
    print "        Percentage Increase from Organic: " + str(round((total_organic_installs / float(number_of_new_users_over_this_period)) * 100, 2)) + "%"
    print "        Percentage Increase from Non-referral Promo: " + str(round((total_nonreferral_promo_installs / float(number_of_new_users_over_this_period)) * 100, 2)) + "%"
    print "        Percentage Increase from Website: " + str(round((total_website_installs / float(number_of_new_users_over_this_period)) * 100, 2)) + "%"
    print "        Percentage Increase from Download Invite: " + str(round((total_download_invite_installs / float(number_of_new_users_over_this_period)) * 100, 2)) + "%"
    print "        Percentage Increase from Event Invite: " + str(round((total_event_invite_installs / float(number_of_new_users_over_this_period)) * 100, 2)) + "%"
    print "        Percentage Increase from Referral Promo: " + str(round((total_referral_promo_installs / float(number_of_new_users_over_this_period)) * 100, 2)) + "%"
    print ""
    print "--------------------------------------------"

    new_users_sending_download_invites = []
    for user in new_users_over_this_period:
        if total_contact_statuses.filter(referring_user=user).exists():
            new_users_sending_download_invites.append(user)
    number_of_new_users_sending_download_invites = len(new_users_sending_download_invites)
    average_number_of_download_invites_sent_per_new_user = total_download_invite_uniques / float(number_of_new_users_over_this_period)

    print ""
    print "Virality of Download Invites:"
    print "    Number of Unique Download Invitations Sent Over This Period: " + str(total_download_invite_uniques)
    print "    Number of Download Invitation Installs Over This Period: " + str(total_download_invite_installs)
    print "    Download Referrals Conversion Rate: " + str(round(total_download_invite_conversion_rate * 100, 2)) + "%"
    print "    Number of New Users: " + str(number_of_new_users_over_this_period)
    print "    Number of New Users Sending Download Invites: " + str(number_of_new_users_sending_download_invites)
    print "    Percent of New Users Sending Download Invites: " + str(round((number_of_new_users_sending_download_invites / float(number_of_new_users_over_this_period)) * 100, 2)) + "%"
    print "    Average Number of Download Invitations Sent per Inviting New User: " + str(round(total_download_invite_uniques / float(number_of_new_users_sending_download_invites), 2))
    print "    Average Number of Download Invitations Sent per New User: " + str(round(average_number_of_download_invites_sent_per_new_user, 2))
    print "    Viral Coefficient: " + str(round(average_number_of_download_invites_sent_per_new_user * total_download_invite_conversion_rate, 2))
    print "    Viral Coefficient: " + str(round(average_number_of_download_invites_sent_per_new_user * total_download_invite_conversion_rate, 2))

def seattle_users_ios(min_date=datetime(2013, 1, 1), max_date=datetime.now()):
    seattle_users = get_user_within_distance(47.66759, -122.312766, 20)
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

def users_w_redemptions(users):
    venues = get_venues_within_distance(47.66759, -122.312766, 20)
    deals = Deal.objects.filter(place__in=venues, active=True, in_app_payment=True)
    hotspots = Beacon.objects.filter(creator_id__in=users, date_created__lt=datetime.now()).exclude(cancelled=True)
    redeemed_deals = DealStatus.objects.filter(beacon__in=hotspots, deal_status=DEAL_STATUS.REDEEMED)
    users_w_redemption = []
    for x in redeemed_deals:
        if x.user:
            if x.user not in users_w_redemption:
                users_w_redemption.append(x.user)
    return users_w_redemption

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

def get_venue_stats(min_date=(datetime.now() - timedelta(days=30)), max_date=datetime.now() - timedelta(seconds=1)):
    venues = get_venues_within_distance(47.66759, -122.312766, 20)
    print "venue, tot_redemptions, paid_redemptions, amt owed, public_checkins, followers"
    for venue in venues:
        deals = Deal.objects.filter(place=venue)
        deal_statuses = DealStatus.objects.filter(deal__in=deals, date_created__gte=min_date, date_created__lt=max_date).exclude(user__in=excluded_users).exclude(deal__in=excluded_deals)
        public_checkins = deal_statuses.filter(public=True)
        tot_redemptions = deal_statuses.filter(deal_status=DEAL_STATUS.REDEEMED)
        paid_redemptions = tot_redemptions.exclude(payment_authorization="REWARD")
        favorites = Favorites.objects.filter(place=venue, active=True)
        unique_followers = favorites.values_list('user').distinct()
        revenue = 0
        for deal in deals:
            items = tot_redemptions.filter(deal=deal)
            revenue = revenue + (len(items) * deal.item_cost)
        print venue.name + ", {0}, {1}, ${2}, {3}, {4}".format(len(tot_redemptions), len(paid_redemptions), str(revenue), len(public_checkins), len(unique_followers))
        #print venue.name + " from {0} to {1}:".format(str(min_date.strftime("%Y-%m-%d")), str(max_date.strftime("%Y-%m-%d")))
        #print "Total redemptions: {0} ({1} paid) for ${2}; {3} public checkins; {4} followers".format(len(tot_redemptions), len(paid_redemptions), str(revenue), len(public_checkins), len(unique_followers))

promo_dct = {
        'seattlebg1': {'id': 102, 'venue': 'Bleu Grotto', 'name': 'Sam Sparks', 'contact': 'samjsparks@yahoo.com', 'users': [], 'redemptions':[]},
        'seattlebg2': {'id': 102, 'venue': 'Bleu Grotto', 'name': 'Sarah Dennis', 'contact': 'sarahdennis1@outlook.com', 'users': [], 'redemptions':[]},
        'seattlebg3': {'id': 91, 'venue': 'Kesslers', 'name': 'Denise Kathleen', 'contact': 'denisekathleen78@gmail.com', 'users': [],'redemptions':[]},
        'seattlebg4': {'id': 102, 'venue': 'Bleu Grotto', 'name': 'Ross McCartney', 'contact': '2062343087', 'users': [], 'redemptions':[]},
        'ballroom1': {'id': 100, 'venue': 'Ballroom', 'name': 'Cynthia Huntley', 'contact': 'cynthia3614@gmail.com', 'users': [], 'redemptions':[]},
        'ballroom2': {'id': 100, 'venue': 'Ballroom', 'name': 'TBD', 'contact': 'TBD', 'users': [], 'redemptions':[]},
        'seattlebl1': {'id': 100, 'venue': 'Ballroom', 'name': 'Tamara Rose', 'contact': 'tamara@ballroomfremont.com', 'users': [], 'redemptions':[]},
        'seattlebl2': {'id': 100, 'venue': 'Ballroom', 'name': 'Collette Kitchell', 'contact': 'collettekitchell@aol.com', 'users': [], 'redemptions':[]},
        'seattlebl3': {'id': 100, 'venue': 'Ballroom', 'name': 'Nate Thomas', 'contact': 'Nathaniell.thomas@gmail.com', 'users': [], 'redemptions':[]},
        'seattlebl4': {'id': 100, 'venue': 'Ballroom', 'name': 'Cynthia Huntley', 'contact': 'cynthia3614@gmail.com', 'users': [], 'redemptions':[]},
        'seattlebl5': {'id': 100, 'venue': 'Ballroom', 'name': 'Collette Kitchell (2nd set)', 'contact': 'collettekitchell@aol.com', 'users': [], 'redemptions':[]},
        'seattlebl6': {'id': 100, 'venue': 'Ballroom', 'name': 'Jake Cabrales', 'contact': 'jcab81@gmail.com', 'users': [], 'redemptions':[]},
        'seattlebl7': {'id': 100, 'venue': 'Ballroom', 'name': 'Drew Kurata', 'contact': 'kurata_13@hotmail.com', 'users': [], 'redemptions':[]},
        'seattleba1': {'id': 100, 'venue': 'Ballroom', 'name': 'UNCLAIMED', 'contact': 'NA', 'users': [], 'redemptions':[]},
        'seattleba2': {'id': 100, 'venue': 'Ballroom', 'name': 'UNCLAIMED', 'contact': 'NA', 'users': [], 'redemptions':[]},
        'seattleba3': {'id': 100, 'venue': 'Ballroom', 'name': 'UNCLAIMED', 'contact': 'NA', 'users': [], 'redemptions':[]},
        'seattleba4': {'id': 19983, 'venue': 'Blue Moon Tavern', 'name': 'Tim Hotchkin', 'contact': 'djmot67@gmail.com', 'users': [], 'redemptions':[]},
        'seattlepie1': {'id': 113, 'venue': 'Pie Bar', 'name': 'Kelly Patrick', 'contact': 'Kellyy.kpat@gmail.com', 'users': [], 'redemptions':[]},
        'seattlepie2': {'id': 113, 'venue': 'Pie Bar', 'name': 'UNCLAIMED', 'contact': 'NA', 'users': [], 'redemptions':[]},
        'seattlepie3': {'id': 113, 'venue': 'Pie Bar', 'name': 'UNCLAIMED', 'contact': 'NA', 'users': [], 'redemptions':[]},
        'seattlepie4': {'id': 113, 'venue': 'Pie Bar', 'name': 'Robin LaChance', 'contact': 'winddancer78@hotmail.com', 'users': [], 'redemptions':[]},
        'changes1': {'id': 93, 'venue': 'Changes', 'name': 'UNCLAIMED', 'contact': 'NA', 'users': [], 'redemptions':[]},
        'changes2': {'id': 93, 'venue': 'Changes', 'name': 'UNCLAIMED', 'contact': 'NA', 'users': [], 'redemptions':[]},
        'changes3': {'id': 93, 'venue': 'Changes', 'name': 'UNCLAIMED', 'contact': 'NA', 'users': [], 'redemptions':[]},
        'changes4': {'id': 93, 'venue': 'Changes', 'name': 'UNCLAIMED', 'contact': 'NA', 'users': [], 'redemptions':[]},
        'kessler1': {'id': 91, 'venue': 'Kesslers', 'name': 'Denise Kathleen', 'contact': 'denisekathleen78@gmail.com', 'users': [], 'redemptions':[]},
        'kessler2': {'id': 91, 'venue': 'Kesslers', 'name': 'Tracy Ward', 'contact': '555kess@gmail.com', 'users': [], 'redemptions':[]},
        'kessler3': {'id': 91, 'venue': 'Kesslers', 'name': 'UNCLAIMED', 'contact': 'NA', 'users': [], 'redemptions':[]},
        'clever1': {'id': 115, 'venue': 'Clever Dunnes', 'name': 'UNCLAIMED', 'contact': 'NA', 'users': [], 'redemptions':[]},
        'clever2': {'id': 115, 'venue': 'Clever Dunnes', 'name': 'UNCLAIMED', 'contact': 'NA', 'users': [], 'redemptions':[]},
        'clever3': {'id': 115, 'venue': 'Clever Dunnes', 'name': 'UNCLAIMED', 'contact': 'NA', 'users': [], 'redemptions':[]},
        'clever4': {'id': 115, 'venue': 'Clever Dunnes', 'name': 'UNCLAIMED', 'contact': 'NA', 'users': [], 'redemptions':[]}
}

def get_drink_card_stats(min_date=(datetime.now() - timedelta(weeks=1)), max_date=datetime.now()):
    reward_items = get_drink_card_reward_items(min_date, max_date)
    for reward in reward_items:
        user = reward.user
        promo_dct[reward.promo_code]['users'].append(user)
        redemptions = DealStatus.objects.filter(user=user, deal_status=DEAL_STATUS.REDEEMED, payment_authorization="REWARD")
        promo_dct[reward.promo_code]['redemptions'].append(len(redemptions))
    print "code, venue, name, installs, reward_redemptions"
    for key, value in promo_dct.iteritems():
        if len(value['users']) > 0:
            print key + ", " + value['venue'] + ', ' + value['name'] + ", " + str(len(value['users'])) + ", " + str(len(value['redemptions']))

def get_drink_card_reward_items(min_date, max_date):
    target_promos = promo_dct.keys()
    reward_items = RewardItem.objects.filter(promo_code__in=target_promos, date_created__gte=min_date, date_created__lt=max_date)
    return reward_items

def users_with_number_of_friends(users, min=1):
    users_with_minimum_number_of_friends = []
    for user in users:
        user_friend_phone_numbers = Contact.objects.filter(user=user).values_list('normalized_phone', flat=True)
        friends = User.objects.filter(username__in=user_friend_phone_numbers)
        if len(friends) >= min:
            users_with_minimum_number_of_friends.append(user)
    return users_with_minimum_number_of_friends

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
