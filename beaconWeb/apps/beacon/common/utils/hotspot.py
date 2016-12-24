from datetime import datetime, timedelta
from django.utils.encoding import smart_str
from beaconWeb.common_utils import refetch_model_instance
from beaconWeb.common_utils import distance_between_two_points
from beaconWeb.apps.beacon.models.beacon import Beacon
from beaconWeb.apps.beacon.models.image import Image
from beaconWeb.apps.beacon.models.beacon_follow import BeaconFollow
from beaconWeb.apps.beacon.common.common_utils import parse_json_into_users_and_contact_lists, \
    get_user_hotspot, send_sms_invites, create_hotspot_message_in_chat, is_hotspot_expired, generate_image_url,\
    add_extra_hotspot_properties
from beaconWeb.apps.beacon.common.system_messages import *
from beaconWeb.apps.beacon.common.constants.beacon_status_values import *
from beaconWeb.apps.beacon.tasks.send_sms import send_hotspot_message, send_push_to_wakeup_users
from beaconWeb.apps.beacon.common.utils.login import get_name
from beaconWeb.apps.beacon.common.constants.message_type import MESSAGE_TYPE
from beaconWeb.date_formatter import DateFormatter
from beaconWeb.apps.beacon.common.utils.encryption import simple_int_hash
from beaconWeb.apps.beacon.common.common_utils import fetch_bitly_url
from django.conf import settings
from scheduler import scheduler

#Helper functions
def get_number_of_invites(beacon):
    invites = BeaconFollow.objects.filter(beacon=beacon)
    return len(invites) - 1


def add_extra_hotspot_properties_for_mobile(beacon, beacon_invite):
    contact = beacon_invite.contact
    beacon.invite_number = get_number_of_invites(beacon)
    beacon.image_urls = get_hotspot_images(beacon)
    if BeaconFollow.objects.filter(contact=contact, beacon=beacon).exists():
        beacon_follow = BeaconFollow.objects.filter(contact=contact, beacon=beacon).latest('date_created')
        if beacon_follow.state == BEACON_FOLLOW_STATUS.GOING:
            beacon.follow = True
            return beacon
        else:
            beacon.follow = False
            return beacon
    else:
        beacon.follow = False
        return beacon


def get_hotspot_images(beacon):
    images = Image.objects.filter(beacon=beacon)
    image_urls = []
    for image in images:
        image_urls.append(generate_image_url(image))
    return image_urls


#Main functions
def create_beacon(user, beacon_data, invite_list):
    if not ('time' and 'longitude' and 'latitude' and 'description' and 'address' in beacon_data):
        return False
    date_time = datetime.fromtimestamp(float(beacon_data['time']))
    lat = float(beacon_data['latitude'])
    long = float(beacon_data['longitude'])
    description = smart_str(beacon_data['description'])
    beacon = Beacon(creator=user, description=description,
                        time=date_time, private=False, longitude=long, latitude=lat, address=beacon_data['address'])
    beacon.save()

    creatorIsGoing = BeaconFollow(user=user, beacon=beacon, state=BEACON_FOLLOW_STATUS.GOING)
    creatorIsGoing.save()

    user_list, contact_list = parse_json_into_users_and_contact_lists(user, invite_list)

    numberOfFriends = len(user_list) + len(contact_list)
    if numberOfFriends > 0:
        send_sms_invites(user, beacon, user_list, contact_list)
        chat_message1, avatar_url1 = set_hotspot_message(user)
        chat_message2, avatar_url2 = invite_friends_message(user, numberOfFriends)
        create_hotspot_message_in_chat(beacon, chat_message1, user, None, avatar_url1)
        create_hotspot_message_in_chat(beacon, chat_message2, user, None, avatar_url2)
    else:
        chat_message, avatar_url = set_hotspot_message(user)
        create_hotspot_message_in_chat(beacon, chat_message, user, None, avatar_url)
    return beacon


def create_hotspot(user, latitude, longitude, address, description, time, invite_list, user_latitude=None, user_longitude=None):
    beacon = Beacon(creator=user, description=description,
                        time=time, private=False, longitude=longitude, latitude=latitude, address=address)
    beacon.save()

    creatorIsGoing = BeaconFollow(user=user, beacon=beacon, state=BEACON_FOLLOW_STATUS.GOING)
    if user_latitude:
        distance = distance_between_two_points(latitude, longitude, user_latitude, user_longitude)
        dt = abs(datetime.now() - time).total_seconds()
        if distance < 0.2 and dt < 60*15:
            creatorIsGoing.state = BEACON_FOLLOW_STATUS.HERE

    creatorIsGoing.save()

    user_list, contact_list = parse_json_into_users_and_contact_lists(user, invite_list)

    numberOfFriends = len(user_list) + len(contact_list)
    if numberOfFriends > 0:
        send_sms_invites(user, beacon, user_list, contact_list)
        chat_message1, avatar_url1 = set_hotspot_message(user)
        chat_message2, avatar_url2 = invite_friends_message(user, numberOfFriends)
        create_hotspot_message_in_chat(beacon, chat_message1, user, None, avatar_url1)
        create_hotspot_message_in_chat(beacon, chat_message2, user, None, avatar_url2)
    else:
        chat_message, avatar_url = set_hotspot_message(user)
        create_hotspot_message_in_chat(beacon, chat_message, user, None, avatar_url)
    hotspot_with_extra_properties = add_extra_hotspot_properties(beacon)

    scheduler.enqueue_at(beacon.time, send_push_to_wakeup_users, user_list)
    scheduler.enqueue_at(beacon.time + timedelta(hours=1), send_push_to_wakeup_users, user_list)
    scheduler.enqueue_at(beacon.time + timedelta(hours=2), send_push_to_wakeup_users, user_list)

    if (beacon.time - datetime.now()).total_seconds() > 60*60*2:
        scheduler.enqueue_at(beacon.time - timedelta(minutes=15), send_reminder, beacon)

    return hotspot_with_extra_properties


def hotspot_webview_url(beacon_follow):
    hashed_invite_id = simple_int_hash(beacon_follow.pk)
    shortened_url = "{0}/hotspot/{1}".format(settings.URL, hashed_invite_id)
    shortened_url = fetch_bitly_url(shortened_url)
    shortened_url = shortened_url.strip('http://')
    return shortened_url


def deal_webview_url(deal_status):
    hashed_invite_id = simple_int_hash(deal_status.pk)
    shortened_url = "{0}/hotspot-deal/{1}".format(settings.URL, hashed_invite_id)
    print shortened_url
    shortened_url = fetch_bitly_url(shortened_url)
    print shortened_url
    # shortened_url = shortened_url.strip('http://')
    return shortened_url

def get_hotspot_for_mobile_view(data_request):
    if not ('beacon_invite' in data_request):
        return False
    beacon_follow_id = data_request['beacon_invite']
    beacon_follow = BeaconFollow.objects.get(pk=beacon_follow_id)
    beacon = beacon_follow.beacon
    hotspotWithExtraProperties = add_extra_hotspot_properties_for_mobile(beacon, beacon_follow)
    return hotspotWithExtraProperties


def change_hotspot(user, request_data):
    if not ('beacon_id' in request_data):
        return False
    beacon = Beacon.objects.get(pk=request_data['beacon_id'])
    if 'cancelled' in request_data:
        changed_beacon = cancel_hotspot(user, beacon)
    else:
        changed_beacon = update_hotspot(user, beacon, request_data)
    hotspot_with_extra_properties = add_extra_hotspot_properties(changed_beacon)
    return hotspot_with_extra_properties


def cancel_hotspot(user, beacon):
    beacon.cancelled = True
    beacon.save()
    name = get_name(user)
    sms_message = smart_format("{0} cancelled their Hotspot", name)
    push_message = smart_format("{0} cancelled their Hotspot", name)
    change_hotspot_message(beacon, sms_message, push_message)
    return beacon


def send_reminder(beacon):
    #usually queued on scheduler, so refresh object
    beacon = refetch_model_instance(beacon)
    if beacon.cancelled:
        return
    beacon_follows = BeaconFollow.objects.filter(beacon=beacon).exclude(state=BEACON_FOLLOW_STATUS.DECLINED).\
        select_related('user', 'contact')
    time_string = DateFormatter().friendly_string_for_timestamp(beacon.beacon_time, beacon.latitude, beacon.longitude)
    text = smart_format("Reminder: {0}\n{1} @ {2}", beacon.description, time_string, beacon.address)
    users = []
    contacts = []
    for b in beacon_follows:
        if b.user:
            users.append(b.user)
        else:
            contacts.append(b.contact)
    #        for now message type is MESSAGE in order to open to correct hotspot
    send_hotspot_message(users=users, push_text=text, contacts=contacts, sms_text=text, message_type=MESSAGE_TYPE.MESSAGE, beacon_id=beacon.pk)




def change_hotspot_message(beacon, sms_message, push_message):
    bf_objects = BeaconFollow.objects.filter(beacon=beacon).select_related('user', 'contact')
    users = []
    contacts = []
    print
    for bf in bf_objects:
        if bf.user:
            users.append(bf.user)
        elif bf.contact:
            contacts.append(bf.contact)

    users.remove(beacon.creator)
    send_hotspot_message.delay(users, push_message, contacts, sms_message, MESSAGE_TYPE.HOTSPOT_UPDATE, beacon.id)


def update_hotspot(user, beacon, request_data):
    date_time = datetime.fromtimestamp(float(request_data['time']))
    lat = float(request_data['latitude'])
    long = float(request_data['longitude'])
    beacon.description = request_data['description']
    beacon.time = date_time
    beacon.latitude = lat
    beacon.longitude = long
    beacon.address = request_data['address']
    beacon.save()
    name = get_name(user)
    chat_message = smart_format("{0} updated this Hotspot", name)
    sms_message = smart_format("{0} updated their Hotspot\nHotspot://Go-to-App", name)
    push_message = smart_format("{0} updated their Hotspot", name)
    change_hotspot_message(beacon, sms_message, push_message)
    create_hotspot_message_in_chat(beacon, chat_message, user, None, avatar_url=HOTBOT_AVATAR.HAPPY)
    return beacon


def get_hotspot(beacon_id):
    beacon = Beacon.objects.get(pk=beacon_id)
    hotspotWithExtraProperties = add_extra_hotspot_properties(beacon)
    return hotspotWithExtraProperties
