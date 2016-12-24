from beaconWeb.apps.beacon.models.profile import Profile
from beaconWeb.apps.beacon.models.contact import Contact
from beaconWeb.apps.beacon.tasks.send_sms import send_hotspot_message
from beaconWeb.apps.beacon.common.constants.message_type import MESSAGE_TYPE
from django_rq import job
from beaconWeb.settings import RQ_THREAD
from django.conf import settings
from beaconWeb.apps.beacon.common.utils.tracker import track_notification
from beaconWeb.apps.beacon.common.constants.notification_types import NOTIFICATION_TYPE


#helper functions
def get_name(user):
    if user.last_name == "":
        return user.first_name
    else:
        return user.first_name + " " + user.last_name


#Main functions
@job(RQ_THREAD)
def send_push_that_friend_joined(profile):
    # name = get_name(profile.user)
    new_user_contacts_objects = get_friend_contact_objects(profile)
    # newUserFriendList = []
    for contact in new_user_contacts_objects:
        message = "{0} just joined Hotspot".format(contact.name)
        send_unique_push_message(contact.user, message, NOTIFICATION_TYPE.FRIEND_JOINED_PUSH, profile.user)


@job(RQ_THREAD)
def get_friend_contact_objects(profile):
    new_user_phone_number = profile.normalized_phone
    new_user_contacts_objects = Contact.objects.filter(normalized_phone=new_user_phone_number).select_related('user')
    return new_user_contacts_objects


@job(RQ_THREAD)
def send_unique_push_message(recipient_user, message, type, sending_user):
    # if settings.ENVIRONMENT and settings.ENVIRONMENT == 'Production':
    send_hotspot_message(users=[recipient_user], push_text=message, message_type=MESSAGE_TYPE.GENERAL)
    track_notification(recipient_user, NOTIFICATION_TYPE.FRIEND_JOINED_PUSH, message, sending_user)