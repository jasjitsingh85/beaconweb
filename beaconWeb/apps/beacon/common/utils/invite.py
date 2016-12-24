from beaconWeb.apps.beacon.common.common_utils import parse_json_into_users_and_contact_lists, send_sms_invites,\
    create_hotspot_message_in_chat, get_hotspot_guests
from beaconWeb.apps.beacon.tasks.send_sms import send_hotspot_message
from beaconWeb.apps.beacon.common.constants.message_type import MESSAGE_TYPE
from beaconWeb.apps.beacon.models.beacon import Beacon
from beaconWeb.apps.beacon.models.deal_status import DealStatus
from beaconWeb.apps.beacon.models.beacon_follow import BeaconFollow
from beaconWeb.apps.beacon.common.constants.beacon_status_values import BEACON_FOLLOW_STATUS
from beaconWeb.apps.beacon.models.deal import Deal
from beaconWeb.apps.beacon.common.system_messages import invite_friends_message
from beaconWeb.common_utils import smart_format
from beaconWeb.apps.beacon.common.utils.deals import deal_hours_for_datetime, send_deal_invites, update_deal_statuses_for_beacon
import datetime
import calendar
from beaconWeb.geo_timezone import GeoTimeZone

#Helper functions
def add_names_to_list(user_list, contact_list):
    list_of_names = []

    for user in user_list:
        name = user.first_name + " " + user.last_name
        list_of_names.append(name)

    for contact in contact_list:
        name = contact.name
        list_of_names.append(name)

    return list_of_names


def remove_duplicate_contacts(contact_list):
    updated_contact_list = []
    phone_numbers = []
    for contact in contact_list:
        if contact.normalized_phone not in phone_numbers:
            phone_numbers.append(contact.normalized_phone)
            updated_contact_list.append(contact)
    return updated_contact_list

#Main functions
def invite_friends(user, beacon, invite_list, message=None):
    if DealStatus.objects.filter(beacon=beacon).exists():
        deal_status = DealStatus.objects.filter(beacon=beacon, user=user)[0]
        deal_id = deal_status.deal.id
        deal = Deal.objects.get(pk=deal_id)
        #beacon_datetime = datetime.datetime.fromtimestamp(timestamp)
        # deal = Deal.objects.select_related('place').get(pk=deal_id)
        # place = deal.place
        # description = smart_format("Deal at {0}", place.name)

        #get deal hours
        timezone = GeoTimeZone().get_timezone(latitude=beacon.latitude, longitude=beacon.longitude)
        timestamp = calendar.timegm(deal_status.start.timetuple())
        beacon_datetime = datetime.datetime.fromtimestamp(timestamp, tz=timezone)
        # beacon_datetime = deal_status.start
        today_time = 60*60*beacon_datetime.hour + 60*beacon_datetime.minute + beacon_datetime.second

        deal_hours = deal_hours_for_datetime(deal, beacon.time)
        # start = beacon_datetime + datetime.timedelta(seconds=deal_hours.start - today_time)
        start = deal_status.start
        end = deal_status.end
        #create deal status and beacon status objects
        user_list, contact_list = parse_json_into_users_and_contact_lists(user, invite_list)
        beacon_follows = []
        deal_statuses = []
        cleaned_contact_list = remove_duplicate_contacts(contact_list)
        #create deal status and beacon follow for creator
        # deal_statuses.append(DealStatus(deal=deal, beacon=beacon, user=user, hours=deal_hours, start=start, end=end))
        # beacon_follows.append(BeaconFollow(beacon=beacon, user=user, state=BEACON_FOLLOW_STATUS.GOING))
        for invited_user in user_list:
            deal_statuses.append(DealStatus(deal=deal, beacon=beacon, user=invited_user, invited_by=user, hours=deal_hours, start=start, end=end))
            beacon_follows.append(BeaconFollow(beacon=beacon, user=invited_user, invited_by=user))
        for invited_contact in cleaned_contact_list:
            deal_statuses.append(DealStatus(deal=deal, beacon=beacon, contact=invited_contact, invited_by=user, hours=deal_hours, start=start, end=end))
            beacon_follows.append(BeaconFollow(beacon=beacon, contact=invited_contact, invited_by=user))
        BeaconFollow.objects.bulk_create(beacon_follows)
        DealStatus.objects.bulk_create(deal_statuses)
        update_deal_statuses_for_beacon(beacon, deal)

        #send invitations
        if message is None:
            send_deal_invites.delay(deal_statuses, beacon.custom_deal_message)
        else:
            send_deal_invites.delay(deal_statuses, message, user)
        return True
    else:
        # invite more people to this Beacon if the new follower included an invite list
        user_list, contact_list = parse_json_into_users_and_contact_lists(user, invite_list)
        numberOfInvites = len(user_list) + len(contact_list)
        if numberOfInvites > 0:
            send_sms_invites(user, beacon, user_list, contact_list)
            chat_message, avatar_url = invite_friends_message(user, numberOfInvites)
            if beacon.creator != user:
                send_hotspot_message(users=[beacon.creator], push_text=chat_message,
                                     message_type=MESSAGE_TYPE.HOTSPOT_UPDATE, beacon_id=beacon.id)
            create_hotspot_message_in_chat(beacon, chat_message, user, None, avatar_url)
        return True


def get_guestlist_for_mobileview(beacon_id):
    beacon = Beacon.objects.get(pk=beacon_id)
    guests = get_hotspot_guests(beacon)
    here_list = []
    going_list = []
    invited_list = []
    for g in guests:
        if g.profile:
            name = g.profile.user.first_name
            if g.profile.user.last_name:
                name = smart_format("{0} {1}", name, g.profile.user.last_name)
        else:
            name = g.contact.name
        if g.status == 'here':
            here_list.append(name)
        elif g.status == 'going':
            going_list.append(name)
        else:
            invited_list.append(name)

    return here_list, going_list, invited_list