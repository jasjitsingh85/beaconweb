#from beaconWeb.apps.beacon.models.beacon_invite import BeaconInvite
from beaconWeb.common_utils import smart_format
from beaconWeb.apps.beacon.models.beacon_follow import BeaconFollow
from beaconWeb.apps.beacon.models.message import Message
from beaconWeb.apps.beacon.models.event_status import EventStatus
from beaconWeb.apps.beacon.common.constants.event_status import EVENT_STATUS
from beaconWeb.apps.beacon.models.beacon import Beacon
from beaconWeb.apps.push_notifications.models import AndroidDevice
from django.contrib.auth.models import User
from django.db.models import Q
from beaconWeb.apps.beacon.models.sponsored_event import SponsoredEvent
from beaconWeb.apps.beacon.common.common_utils import users_to_notify, generate_image_url
from beaconWeb.apps.beacon.common.utils.friends import get_all_filtered_contacts_for_user
from beaconWeb.apps.beacon.tasks.send_sms import send_hotspot_message, send_hotspot_push
from beaconWeb.apps.beacon.common.constants.message_type import MESSAGE_TYPE
from beaconWeb.apps.beacon.common.constants.chat_type import CHAT_TYPE


#Helper functions
def send_message_notification(beacon, message, name):
    message_text = smart_format("{0}: {1}", name, message.message)
    users = users_to_notify(beacon, message.user)
    send_hotspot_message.delay(users=users, push_text=message_text, message_type=MESSAGE_TYPE.MESSAGE, beacon_id=beacon.id)


def avatar_url(user_id):
    index = (user_id % 20) + 1
    avatar_url = "https://s3.amazonaws.com/hotspot-avatars/{0}.png".format(index)
    return avatar_url


def add_extra_message_properties(message):
    if message.user is not None:
        if message.chat_type == CHAT_TYPE.HOTSPOT_MESSAGE:
            message.profile_pic = message.avatar_url
        else:
            message.profile_pic = avatar_url(message.user.id)
        message.sender = message.user.profile
        message.contact = None
    elif message.contact is not None:
        if message.chat_type == CHAT_TYPE.HOTSPOT_MESSAGE:
            message.profile_pic = message.avatar_url
        else:
            message.profile_pic = avatar_url(message.contact.id)
        #message.contact = Contact.objects.get(pk=message.contact_id)
        message.sender = None
    else:
        message.contact = None
        message.sender = None
        message.profile_pic = None


#Main functions
def store_contact_message(data_request):
    if not ('beacon_invite' and 'message' in data_request):
        return False
    follow_id = data_request['beacon_invite']
    message = data_request['message']
    beacon_invite = BeaconFollow.objects.get(pk=follow_id)
    beacon = beacon_invite.beacon
    contact = beacon_invite.contact
    message = Message.objects.create(beacon=beacon, contact=contact, message=message)
    first_name = contact.name.split()[0]
    send_message_notification(beacon, message, first_name)
    return True


def store_message(user, data_request):
    if not ('event_id' in data_request):
        return False
    event_id = data_request['event_id']
    sponsored_event = SponsoredEvent.objects.get(pk=event_id)
    if 'message' in data_request:
        message_content = data_request['message']
        message = Message.objects.create(event=sponsored_event, user=user, message=message_content)
    elif 'image_url' in data_request:
        message_content = data_request['image_url']
        message = Message.objects.create(event=sponsored_event, user=user, image_url=message_content)
    send_message_notification_to_users(message)


def send_message_notification_to_users(message):
    user = message.user
    event = message.event
    users_to_notify_of_message = get_users_to_notify_of_message(message)
    if message.message:
        push_message = "{0} sent a message in the chatroom for {1} at {2}".replace("{0}", user.get_full_name())\
            .replace("{1}", event.item_name.lower()).replace("{2}", event.place.name)
    else:
        push_message = "{0} added a picture to the chatroom for {1} at {2}".replace("{0}", user.get_full_name())\
            .replace("{1}", event.item_name.lower()).replace("{2}", event.place.name)
    send_notifications(users_to_notify_of_message, push_message, event)


def send_notifications(users, push_message, event):
    for user in users:
        send_hotspot_push([user], push_message, "EventChat", None, None, event.id)


def get_users_to_notify_of_message(message):
    user = message.user
    event = message.event
    last_three_users = Message.objects.filter(date_created__lt=message.date_created, event=message.event).distinct('user').values_list('user', flat=True)[:3]
    android_user_ids = AndroidDevice.objects.all().values_list('user', flat=True)
    contacts = get_all_filtered_contacts_for_user(user)
    contacts_at_event = EventStatus.objects.filter(user__in=contacts, event=event).filter(Q(status=EVENT_STATUS.GOING) | Q(status=EVENT_STATUS.REDEEMED)).values_list('user', flat=True)
    users_to_notify_of_message = User.objects.filter(pk__in=contacts_at_event).exclude(pk__in=android_user_ids)
    return users_to_notify_of_message


def get_message_thread(request):
    if not ('beacon' in request):
        return False
    beacon_id = request['beacon']
    beacon = Beacon.objects.get(pk=beacon_id)
    message_thread = Message.objects.filter(beacon=beacon).exclude(user=None, contact=None).\
        select_related('user', 'user__profile', 'contact').order_by('date_created')
    message_thread_with_extra_properties = []
    for message in message_thread:
        add_extra_message_properties(message)
        if message.image:
            message.image.image_url = generate_image_url(message.image)
        message_thread_with_extra_properties.append(message)
    return message_thread_with_extra_properties