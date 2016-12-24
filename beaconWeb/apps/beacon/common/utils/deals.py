from beaconWeb.apps.beacon.models import Beacon, Deal, DealPlace, DealStatus, DealHours, BeaconFollow, RegionState, ContactStatus, Contact, SyndicatedDeal, Favorites, Location, Tab, TabItem, NotificationTracker
# from beaconWeb.apps.happy_hours.models import HappyHour, Place
from beaconWeb.date_formatter import DateFormatter
from django.contrib.auth.models import User
from beaconWeb.common_utils import smart_format
from beaconWeb.apps.beacon.common.common_utils import parse_json_into_users_and_contact_lists, get_users_within_distance
from beaconWeb.apps.beacon.common.constants.deal_status import DEAL_STATUS
from beaconWeb.apps.beacon.common.constants.beacon_status_values import BEACON_FOLLOW_STATUS
from beaconWeb.apps.beacon.tasks.send_sms import send_sms, send_hotspot_push
from beaconWeb.apps.beacon.tasks.send_sms import send_hotspot_message, send_hotspot_deal_invitations
from beaconWeb.common_utils import distance_between_two_points
from beaconWeb.geo_timezone import GeoTimeZone

import datetime
import pytz
import requests
import json
from django_rq import job
from beaconWeb.settings import RQ_THREAD
from beaconWeb.apps.beacon.common.constants.message_type import MESSAGE_TYPE
from beaconWeb.apps.beacon.common.utils.tracker import track_notification
from beaconWeb.apps.beacon.common.utils.friends import get_friends
from beaconWeb.apps.beacon.common.constants.notification_types import NOTIFICATION_TYPE
from beaconWeb.apps.beacon.common.utils.point_of_sale import create_tab, user_has_open_tab, get_active_deal_for_place
import calendar

@job(RQ_THREAD)
def send_deal_invites(deal_statuses, custom_message=None, invited_by=None):
    beacon = deal_statuses[0].beacon
    deal = deal_statuses[0].deal
    if deal_statuses[0].image_url != '':
        image_url = deal_statuses[0].image_url
    else:
        image_url = None
    if invited_by is None:
        creator = beacon.creator
    else:
        creator = invited_by
    time_string = DateFormatter().friendly_string_for_timestamp(beacon.beacon_time, beacon.latitude, beacon.longitude)
    time_string = time_string[0].lower() + time_string[1:]
    time_string = time_string.replace(',', ' at')
    # sms_message = deal_invite_message(deal, beacon, time_string, is_sms=True, custom_message=custom_message)
    push_message = deal_invite_message(deal, beacon, time_string, is_sms=False, custom_message=custom_message, invited_by=creator)
    sms_message = sms_deal_invitation_message(deal, beacon, False, custom_message=custom_message, invited_by=creator)
    # user_sms_message = sms_deal_invitation_message(deal, beacon, True, custom_message=custom_message)
    # push_message = deal_invite_message(deal, beacon, time_string, is_sms=False, custom_message=custom_message)

    users = []
    contacts = []
    for status in deal_statuses:
        if status.user:
            if status.user.pk != creator.pk:
                users.append(status.user)
        else:
            contacts.append(status.contact)

    # send_hotspot_deal_invitations(users=users, contacts=contacts, sms_text=sms_message)
    # send_hotspot_deal_invitations(users=users, contacts=contacts, user_sms_text=user_sms_message, contact_sms_text=contact_sms_message)
    # send_intro_message_to_relevant_contacts(beacon.creator, contacts)
    send_hotspot_message.delay(users=users, push_text=push_message, contacts=contacts, sms_text=sms_message,
                          beacon_id=beacon.id, message_type=MESSAGE_TYPE.MESSAGE, image_url=image_url)


# def send_intro_message_to_relevant_contacts(creator, contacts):
#     sms_text = smart_format("{0} is texting you through Hotspot to meet-up (and save money)\n\nLearn more: GetHotspotApp.com", creator.get_full_name())
#     first_time_contacts = get_first_time_contacts(contacts)
#     print "First time contacts:" + str(first_time_contacts)
#     print sms_text
#     send_sms(sms_text, first_time_contacts)


@job(RQ_THREAD)
def notify_friends_of_user_for_deal(deal_status, isPresent):
    # user_name = deal_status.user.get_full_name()
    venue_name = deal_status.deal.place.name
    sending_user = deal_status.user
    users_to_invite_ids, blocked_friend_ids = get_friends(sending_user)
    users_to_invite = User.objects.filter(pk__in=users_to_invite_ids)
    for user in users_to_invite:
        message = get_social_message(sending_user.get_full_name(), venue_name, deal_status.deal.item_price, deal_status.deal.item_name, isPresent)
        send_notification(user, message, sending_user)


@job(RQ_THREAD)
def notify_friends_of_user_for_event(event_status):
    venue_name = event_status.event.place.name
    sending_user = event_status.user
    date_string = get_date_string_for_event(event_status.event.start)
    users_to_invite_ids, blocked_friend_ids = get_friends(sending_user)
    users_to_invite = User.objects.filter(pk__in=users_to_invite_ids)
    for user in users_to_invite:
        message = get_social_message_for_event_reservation(sending_user.get_full_name(), event_status.event.title, venue_name, date_string)
        send_notification_for_event(user, message, sending_user, event_status.event)


def get_date_string_for_event(event_start):
    now = datetime.datetime.now()
    if (now + datetime.timedelta(weeks=1)) > event_start:
        return calendar.day_name[event_start.weekday()]
    else:
        return event_start.strftime("%B %d")


def get_social_message_for_event_reservation(contact_name, event_title, event_venue, event_date):
    return "{0} is going to the {1} event at {2} on {3}".replace("{0}", contact_name).replace("{1}", event_title).replace("{2}", event_venue).replace("{3}", event_date)


def get_social_message(contact_name, venue_name, item_price, item_name, isPresent):
    if isPresent:
        return "{0} is at {1}. Join them for a ${2} {3}".replace("{0}", contact_name).replace("{1}", venue_name).replace("{2}", str(format(item_price, '.2f'))).replace("{3}", item_name.lower())
    else:
        return "{0} is going to {1}. Join them for a ${2} {3}".replace("{0}", contact_name).replace("{1}", venue_name).replace("{2}", str(format(item_price, '.2f'))).replace("{3}", item_name.lower())


def send_notification(invited_user, message, sending_user):
    # users_to_invite = get_users_to_invite(user, lat, lng)
    # for invited_user in users_to_invite:
    send_hotspot_push([invited_user], message)
    track_notification(invited_user, NOTIFICATION_TYPE.FRIEND_INVITED_PUSH, message, sending_user)
    print sending_user.get_full_name()
    print message
    print ""


def send_notification_for_event(invited_user, message, sending_user, event):
    # users_to_invite = get_users_to_invite(user, lat, lng)
    # for invited_user in users_to_invite:
    send_hotspot_push([invited_user], message)
    notification_tracker = NotificationTracker(recipient=invited_user, notification_type=NOTIFICATION_TYPE.EVENT_RESERVED_PUSH,
                                                   notification_detail=message, sender=sending_user, event=event)
    notification_tracker.save()
    print sending_user.get_full_name()
    print message
    print ""


def get_users_to_invite(user, lat, lng):
    users = get_users_within_distance(lat, lng)
    contacts = Contact.objects.filter(user__in=users, normalized_phone=user.profile.normalized_phone)
    return contacts


def get_first_time_contacts(contacts):
    contacts_texted_list = DealStatus.objects.filter(contact__in=contacts, date_created__gte=datetime.datetime.now()-datetime.timedelta(weeks=8)).values_list('contact', flat=True)
    contacts_texted = Contact.objects.filter(pk__in=contacts_texted_list).values_list('normalized_phone', flat=True)
    filtered_contacts = Contact.objects.filter(pk__in=[o.id for o in contacts]).exclude(normalized_phone__in=contacts_texted).values_list('normalized_phone', flat=True)
    return list(set(filtered_contacts))


def sms_deal_invitation_message(deal, beacon, isUser, custom_message=None, invited_by=None):
    # creator = beacon.creator
    if isUser:
        message = smart_format("{0}: {1}\n\nReply 'Yes' to let {2} know you are coming", invited_by.get_full_name(), custom_message, invited_by.first_name)
    else:
        message = smart_format("{0}: {1}\n\nReply 'Yes' to let {2} know you are coming", invited_by.get_full_name(), custom_message, invited_by.first_name)
    return message


def deal_invite_message(deal, beacon, time_string, is_sms=True, custom_message=None, invited_by=None):
    if invited_by is None:
        creator = beacon.creator
    else:
        creator = invited_by
    place_name = deal.place.name
    place_address = deal.place.street_address
    if is_sms and custom_message:
        message = smart_format("{0}: {1}\n\nReply 'Yes' to let {2} know you are coming. {3} is texting you through Hotspot. With the app you'll {4}", creator.get_full_name(), custom_message, creator.first_name, creator.first_name, deal.invite_description)
    elif not is_sms and custom_message:
        message = smart_format("{0}: {1}", creator.get_full_name(), custom_message)
    elif is_sms and not custom_message:
        message = smart_format("{0} invited you to redeem a group deal at {1} ({2}). Join {3} {4} and {5}.\n\nReply with 'Yes' to let {6} know you are coming or 'More' to get more info",
                           creator.get_full_name(), place_name, place_address, creator.first_name,
                           time_string, deal.invite_description, creator.first_name)
    else:
        message = smart_format('{0} invited you to redeem a group deal at {1}. Join {3} {4} and {5}.',
                                 creator.get_full_name(), place_name, place_address, creator.first_name, time_string, deal.invite_description)
    return message


def get_image_url(request_data):
    print "Getting image url"
    if 'image_url' in request_data:
        print "image_url: " + str(request_data['image_url'])
        return request_data['image_url']
    else:
        print "no image_url"
        return None


def invite_friends_to_app(user, invite_list, custom_message):
    user_list, contact_list = parse_json_into_users_and_contact_lists(user, invite_list)
    sms_message = user.first_name + " " + user.last_name + ": " + custom_message
    cleaned_contact_list = remove_duplicate_contacts(contact_list)
    # sent_phone_numbers = []
    for contact in cleaned_contact_list:
        # if contact.normalized_phone not in sent_phone_numbers:
        if not ContactStatus.objects.filter(contact=contact, referring_user=user).exists():
            contact_status = ContactStatus(contact=contact, referring_user=user)
            contact_status.save()
            send_sms(sms_message, [contact.normalized_phone])
            # sent_phone_numbers.append(contact.normalized_phone)


def is_deal_active(user, request_data):
    if 'venue_id' not in request_data:
        return False
    venue_id = int(request_data['venue_id'])
    deals = Deal.objects.filter(place_id=venue_id)
    return not DealStatus.objects.filter(user=user, deal__in=deals, date_created__gt=datetime.datetime.now()-datetime.timedelta(hours=6), deal_status="R").exists()


def check_in_for_deal(user, request_data):
    if 'deal_id' and 'is_present' and "is_public" not in request_data:
        return False
    isPresent = bool(int(request_data['is_present']))
    isPublic = bool(int(request_data['is_public']))
    deal_id = int(request_data['deal_id'])
    deal = Deal.objects.select_related('place').get(pk=deal_id)
    place = deal.place
    description = smart_format("Deal at {0}", place.name)
    time_cutoff = datetime.datetime.now()-datetime.timedelta(hours=6)

    if not DealStatus.objects.filter(deal=deal, user=user, deal_status=DEAL_STATUS.UNLOCKED, date_created__gte=time_cutoff).exists():
        timezone = GeoTimeZone().get_timezone(latitude=place.latitude, longitude=place.longitude)
        beacon_datetime = datetime.datetime.now(tz=timezone)
        today_time = 60*60*beacon_datetime.hour + 60*beacon_datetime.minute + beacon_datetime.second
        beacon = Beacon(creator=user, description=description, place=place, time=beacon_datetime, private=False,
                        longitude=place.longitude, latitude=place.latitude, address=place.street_address)
        beacon.save()

        deal_hours = deal_hours_for_datetime(deal, beacon_datetime)

        start = beacon_datetime
        if deal_hours is None:
            deal_end = beacon_datetime + datetime.timedelta(seconds=86400 - today_time)
        else:
            deal_end = beacon_datetime + datetime.timedelta(seconds=deal_hours.end - today_time)
        end = min(deal_end, start + datetime.timedelta(hours=4))

        deal_status = DealStatus(deal=deal, beacon=beacon, user=user, start=start, end=end, public=isPublic, present=isPresent, deal_status=DEAL_STATUS.UNLOCKED)
        beacon_follow = BeaconFollow(beacon=beacon, user=user, state=BEACON_FOLLOW_STATUS.GOING)

        deal_status.save()
        beacon_follow.save()

        if isPublic:
            notify_friends_of_user_for_deal.delay(deal_status, isPresent)
    else:
        beacon = Beacon.objects.filter(creator=user, description=description, date_created__gte=time_cutoff)[0]

    if deal.reward_eligibility and user.profile.number_of_reward_items > 0:
        deal.is_reward_item = True
    else:
        deal.is_reward_item = False

    deal.is_followed = False

    return deal, beacon


def check_in_for_venue(user, request_data):
    if 'place_id' and "is_public" not in request_data:
        return False

    isPublic = bool(int(request_data['is_public']))
    place_id = int(request_data['place_id'])
    place = DealPlace.objects.get(pk=place_id)
    deal = get_active_deal_for_place(place)
    description = smart_format("Deal at {0}", place.name)
    time_cutoff = datetime.datetime.now()-datetime.timedelta(hours=6)

    if place.has_pos:
        point_of_sale = place.point_of_sale
        if user_has_open_tab(user, point_of_sale):
            tab = Tab.objects.get(user=user, point_of_sale=point_of_sale, closed=False, cancelled=False)
            tab_items = TabItem.objects.filter(tab=tab)
        else:
            tab, tab_items = create_tab(user, request_data)
    else:
        tab = None
        tab_items = None

    if not DealStatus.objects.filter(deal=deal, user=user, deal_status=DEAL_STATUS.UNLOCKED, date_created__gte=time_cutoff).exists():
        timezone = GeoTimeZone().get_timezone(latitude=place.latitude, longitude=place.longitude)
        beacon_datetime = datetime.datetime.now(tz=timezone)
        today_time = 60*60*beacon_datetime.hour + 60*beacon_datetime.minute + beacon_datetime.second
        beacon = Beacon(creator=user, description=description, place=place, time=beacon_datetime, private=False,
                        longitude=place.longitude, latitude=place.latitude, address=place.street_address)
        beacon.save()

        deal_hours = deal_hours_for_datetime(deal, beacon_datetime)

        start = beacon_datetime
        if deal_hours is None:
            deal_end = beacon_datetime + datetime.timedelta(seconds=86400 - today_time)
        else:
            deal_end = beacon_datetime + datetime.timedelta(seconds=deal_hours.end - today_time)
        end = min(deal_end, start + datetime.timedelta(hours=4))

        deal_status = DealStatus(deal=deal, beacon=beacon, user=user, start=start, end=end, public=isPublic, deal_status=DEAL_STATUS.UNLOCKED)
        beacon_follow = BeaconFollow(beacon=beacon, user=user, state=BEACON_FOLLOW_STATUS.GOING)

        deal_status.save()
        beacon_follow.save()

        if isPublic:
            notify_friends_of_user_for_deal.delay(deal_status, False)
    else:
        beacon = Beacon.objects.filter(creator=user, description=description, date_created__gte=time_cutoff).latest('date_created')

    if deal.reward_eligibility and user.profile.number_of_reward_items > 0:
        deal.is_reward_item = True
    else:
        deal.is_reward_item = False

    deal.is_followed = False

    print str(deal)
    print str(beacon)
    print str(tab)
    print str(tab_items)

    return deal, beacon, tab, tab_items


def check_in_for_happy_hour(user, request_data):
    return True


def apply_for_deal(user, deal_id, timestamp, invite_list, custom_message=None, image_url=None):
    #create deal and beacon
    try:
        print "User: " + str(user.id)
        print "deal_id:" + str(deal_id)
        print "Timestamp" + str(timestamp)
    except:
        pass
    #beacon_datetime = datetime.datetime.fromtimestamp(timestamp)
    deal = Deal.objects.select_related('place').get(pk=deal_id)
    place = deal.place
    description = smart_format("Deal at {0}", place.name)

    #get deal hours
    timezone = GeoTimeZone().get_timezone(latitude=place.latitude, longitude=place.longitude)
    beacon_datetime = datetime.datetime.fromtimestamp(timestamp, tz=timezone)
    today_time = 60*60*beacon_datetime.hour + 60*beacon_datetime.minute + beacon_datetime.second

    beacon = Beacon(creator=user, description=description, time=beacon_datetime, private=False,
                    longitude=place.longitude, latitude=place.latitude, address=place.street_address, custom_deal_message=custom_message)
    beacon.save()

    deal_hours = deal_hours_for_datetime(deal, beacon_datetime)
    try:
        print "Deal Hours" + str(deal_hours)
    except:
        pass
    #start = beacon_datetime + datetime.timedelta(seconds=deal_hours.start - today_time)
    start = beacon_datetime
    if deal_hours is None:
        deal_end = beacon_datetime + datetime.timedelta(seconds=86400 - today_time)
    else:
        deal_end = beacon_datetime + datetime.timedelta(seconds=deal_hours.end - today_time)
    end = min(deal_end, start + datetime.timedelta(hours=4))
    #create deal status and beacon status objects
    user_list, contact_list = parse_json_into_users_and_contact_lists(user, invite_list)
    beacon_follows = []
    deal_statuses = []
    #temp hack: throw error if fewer invited than required
    num_invites = len(user_list) + len(contact_list)
    if num_invites < deal.invite_requirement:
        raise Exception('Too Few Invites')
    #create deal status and beacon follow for creator
    deal_statuses.append(DealStatus(deal=deal, beacon=beacon, user=user, start=start, end=end, image_url=image_url))
    beacon_follows.append(BeaconFollow(beacon=beacon, user=user, state=BEACON_FOLLOW_STATUS.GOING))
    cleaned_contact_list = remove_duplicate_contacts(contact_list)
    for invited_user in user_list:
        deal_statuses.append(DealStatus(deal=deal, beacon=beacon, user=invited_user, invited_by=user, start=start, end=end, image_url=image_url))
        beacon_follows.append(BeaconFollow(beacon=beacon, user=invited_user, invited_by=user))
    for invited_contact in cleaned_contact_list:
        deal_statuses.append(DealStatus(deal=deal, beacon=beacon, contact=invited_contact, invited_by=user, start=start, end=end, image_url=image_url))
        beacon_follows.append(BeaconFollow(beacon=beacon, contact=invited_contact, invited_by=user))
    BeaconFollow.objects.bulk_create(beacon_follows)
    DealStatus.objects.bulk_create(deal_statuses)
    update_deal_statuses_for_beacon(beacon, deal)
    create_contact_status_for_deal(beacon)

    if deal.reward_eligibility and user.profile.number_of_reward_items > 0:
        deal.is_reward_item = True
    else:
        deal.is_reward_item = False

    deal.is_followed = False

    #send invitations
    # send_deal_invites(deal_statuses, custom_message)
    send_deal_invites.delay(deal_statuses, custom_message)
    return deal, beacon


def remove_duplicate_contacts(contact_list):
    updated_contact_list = []
    phone_numbers = []
    for contact in contact_list:
        if contact.normalized_phone not in phone_numbers:
            phone_numbers.append(contact.normalized_phone)
            updated_contact_list.append(contact)
    return updated_contact_list


def create_contact_status_for_deal(beacon):
    contact_statuses = []
    for deal_status in beacon.deal_statuses.filter(user=None):
        contact_statuses.append(ContactStatus(deal_status=deal_status))
    ContactStatus.objects.bulk_create(contact_statuses)


def update_deal_statuses_for_beacon(beacon, deal):
    invite_count = beacon.deal_statuses.count()
    if invite_count >= deal.invite_requirement:
        for deal_status in beacon.deal_statuses.all():
            if deal_status.deal_status == DEAL_STATUS.LOCKED:
                deal_status.deal_status = DEAL_STATUS.UNLOCKED
                deal_status.save()


def get_list_of_places_for_user(user, latitude, longitude):
    # place_ids_to_exclude = DealStatus.objects.filter(user=user, date_created__gt=datetime.datetime.now()-datetime.timedelta(hours=6), deal_status="R").values_list('deal__place', flat=True)
    lat_range = [latitude-0.3, latitude+0.3]
    lng_range = [longitude-0.3, longitude+0.3]
    places = list(DealPlace.objects.filter(latitude__range=lat_range, longitude__range=lng_range, closed=False, in_review=False))
    return places



def get_active_deals_at_places(places):
    deals_queryset = Deal.objects.filter(active=True, place_id__in=places, deal_type="DT")
    deals = list(deals_queryset)
    # all_events = Deal.objects.filter(active=True, place_id__in=places).exclude(deal_type="DT")
    filtered_deals = []
    # today_events = []
    if len(deals) > 0:
        timezone = GeoTimeZone().get_timezone(latitude=deals[0].place.latitude, longitude=deals[0].place.longitude)
        now = datetime.datetime.now(tz=timezone)
        weekday = (now.weekday() + 1) % 7
        weekday_bit = [DealHours.days_active.Sunday, DealHours.days_active.Monday, DealHours.days_active.Tuesday,
                       DealHours.days_active.Wednesday, DealHours.days_active.Thursday, DealHours.days_active.Friday,
                       DealHours.days_active.Saturday][weekday]
        now_in_seconds = 60*60*now.hour + 60*now.minute + now.second
        deal_hours = DealHours.objects.filter(deal__in=deals)
        for deal in deals:
            if deal_hours.filter(deal=deal, days_active=weekday_bit, end__gte=now_in_seconds).exists():
                filtered_deals.append(deal)

    return filtered_deals


def nearby_deals(user, latitude, longitude, radius):
    place_ids = get_list_of_places_for_user(user, latitude, longitude)
    if len(place_ids) > 0:
        deals = get_active_deals_at_places(place_ids)
        # deals = Deal.objects.filter(active=True, deal_type="DT").select_related('place')
        # events = get_today_events(all_events)

        user_reward_items = user.profile.number_of_reward_items
        deals = add_favorites_to_deals(user, deals)
        for deal in deals:
            deal.place.distance = distance_between_two_points(latitude, longitude, deal.place.latitude, deal.place.longitude)
            if deal.reward_eligibility and user_reward_items > 0:
                deal.is_reward_item = True
            else:
                deal.is_reward_item = False

        deals.sort(key=lambda x: x.place.distance)

        deals_in_radius = []
        for deal in deals:
            if deal.place.distance < radius:
                deals_in_radius.append(deal)

        # if (len(deals) >= 10) and (len(deals_in_radius) < 10):
        #     return deals[0:10]
        # else:
        #     return deals_in_radius
        return deals
        # deals = list(deals)
        # deals.sort(key=lambda x: place_ids.index(x.place_id))
        # events.sort(key=lambda x: place_ids.index(x.place_id))
    else:
        deals_in_radius = []
        # events = []
    return deals_in_radius


def is_not_duplicate(deal, duplicate_places):
    place_id = deal.place_id
    if place_id in duplicate_places:
        return True
    else:
        return False


def get_today_events(all_events):
    today_events = []
    today = datetime.datetime.now()
    event_deals = all_events.filter(deal_type="EV")
    recurring_deals = all_events.filter(deal_type="RG")
    event_deal_times = DealHours.objects.filter(deal__in=event_deals).select_related('deal')
    recurring_deal_times = DealHours.objects.filter(deal__in=recurring_deals).select_related('deal')
    for time in event_deal_times:
        if time.event_date.date() == today.date():
            today_events.append(time.deal)
    weekday = (today.weekday() + 1) % 7
    weekday_bit = [DealHours.days_active.Sunday, DealHours.days_active.Monday, DealHours.days_active.Tuesday,
                   DealHours.days_active.Wednesday, DealHours.days_active.Thursday, DealHours.days_active.Friday,
                   DealHours.days_active.Saturday][weekday]
    todays_recurring_deal_times = recurring_deal_times.filter(days_active=weekday_bit).select_related('deal')
    for time in todays_recurring_deal_times:
        today_events.append(time.deal)
    return today_events


def get_deal_status(beacon, contact, user):
    if DealStatus.objects.filter(beacon=beacon, contact=contact, user=user).exists():
        deal_status = DealStatus.objects.get(beacon=beacon, contact=contact, user=user)
        return deal_status
    else:
        return None


def deal_hours_for_datetime(deal, date_time):
    # timezone = GeoTimeZone().get_timezone(latitude=deal.place.latitude, longitude=deal.place.longitude)
    # datetime_tz = timezone.localize(date_time)
    weekday = (date_time.weekday() + 1) % 7
    weekday_bit = [DealHours.days_active.Sunday, DealHours.days_active.Monday, DealHours.days_active.Tuesday,
                   DealHours.days_active.Wednesday, DealHours.days_active.Thursday, DealHours.days_active.Friday,
                   DealHours.days_active.Saturday][weekday]
    today_time = 60*60*date_time.hour + 60*date_time.minute + date_time.second
    try:
        print "Today time: " + str(today_time)
        print "Weekday bit: " + str(weekday_bit)
        print "Deal id: " + str(deal.id)
    except:
        pass
    # deal_hours = deal.hours.filter(days_active=weekday_bit)
    deal_hours = deal.hours.filter(start__lte=today_time, end__gte=today_time, days_active=weekday_bit)
    if deal_hours.exists():
        print "Deal Hours Exists"
        return deal_hours[0]
    print "Deal Hours Doesn't Exist"
    return None


def check_user_and_send_repayment_requests(deal_status):
    host = deal_status.beacon.creator
    invitee = deal_status.user
    deal = deal_status.deal
    amount = deal.item_price
    if host.id != invitee.id and deal.in_app_payment:
        if host.profile.is_venmo_enabled:
            make_venmo_request(host, invitee, amount)
        else:
            send_reminder_message(host, invitee, amount)


def send_reminder_message(host, invitee, amount):
    float_amount = "%0.2f" % amount
    message = "Please remember to repay {0} ${1}".format(host.first_name, float_amount)
    send_hotspot_message([invitee], message, [], message)


def make_venmo_request(host, invitee, amount):
    access_token = host.profile.venmo_auth_token
    note = "Repayment for Item via Hotspot"
    phone = invitee.profile.normalized_phone
    venmo_amount = -1 * amount
    url = 'https://api.venmo.com/v1/payments'
    params = {
        "access_token": access_token,
        "phone": phone,
        "note": note,
        "amount": venmo_amount,
    }
    data = {}
    headers = {'Content-Type': 'application/json'}
    try:
        r = requests.post(url, params=params, data=json.dumps(data), headers=headers)
        answer = r.json()
        print answer
    except Exception:
        print "Venmo request failed"


def add_favorites_to_deals(user, deals):
    followed_places = Favorites.objects.filter(user=user, active=True).values_list('place_id', flat=True)
    for deal in deals:
        if deal.place.id in followed_places:
            deal.is_followed = True
        else:
            deal.is_followed = False
    return deals


def nearby_happy_hours(user, latitude, longitude, radius):
    lat_range = [latitude-0.1, latitude+0.1]
    lon_range = [longitude-0.1, longitude+0.1]
    timezone = GeoTimeZone().get_timezone(latitude=latitude, longitude=longitude)
    now = datetime.datetime.now(tz=timezone)
    time_in_seconds = (now.hour * 3600) + (now.minute * 60) + now.second
    bitmask = bitmask_for_day((now.weekday() + 2)%7)
    happy_hours = SyndicatedDeal.objects.filter(days_active=bitmask, place__latitude__range=lat_range, place__longitude__range=lon_range).exclude(place__yelp_id=None).select_related('place')
    # if now and upcoming:
    happy_hours = happy_hours.filter(end__gte=time_in_seconds)
    happy_hours = add_favorites_to_deals(user, happy_hours)
    # elif now:
    #     happy_hours = happy_hours.filter(start__lte=time, end__gte=time)
    # elif upcoming:
    #     happy_hours = happy_hours.filter(start__gte=time)

    happy_hours_in_radius = []
    for happy_hour in happy_hours:
        happy_hour.place.distance = distance_between_two_points(latitude, longitude, happy_hour.place.latitude, happy_hour.place.longitude)
        if happy_hour.place.distance < radius:
            happy_hours_in_radius.append(happy_hour)

    happy_hours_in_radius.sort(key=lambda x: x.place.distance)

    return happy_hours_in_radius

def bitmask_for_day(day):
    days = [SyndicatedDeal.days_active.Sunday,
            SyndicatedDeal.days_active.Monday,
            SyndicatedDeal.days_active.Tuesday,
            SyndicatedDeal.days_active.Wednesday,
            SyndicatedDeal.days_active.Thursday,
            SyndicatedDeal.days_active.Friday,
            SyndicatedDeal.days_active.Saturday]
    return days[day - 1]
