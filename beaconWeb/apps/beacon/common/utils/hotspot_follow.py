from beaconWeb.apps.beacon.models.beacon_follow import BeaconFollow
from beaconWeb.apps.beacon.models.beacon import Beacon
from beaconWeb.apps.beacon.models.profile import Profile
from beaconWeb.apps.beacon.models.contact import Contact
from beaconWeb.apps.beacon.common.system_messages import *
from beaconWeb.apps.beacon.common.common_utils import is_hotspot_expired, \
    add_extra_hotspot_properties, create_hotspot_message_in_chat, send_hotspot_push_to_correct_profiles
from beaconWeb.apps.beacon.common.constants.beacon_status_values import BEACON_FOLLOW_STATUS
from django.contrib.auth.models import User
from beaconWeb.apps.beacon.common.constants.message_type import MESSAGE_TYPE
from beaconWeb.apps.beacon.tasks.send_sms import send_hotspot_message
from datetime import datetime, timedelta



def get_user_or_contact_name(user, contact):
    if user is not None and contact is None:
        return user.first_name
    if contact is not None and user is None:
        return contact.name


def get_list_with_user_hotspot(user):
    hotspot_list = []
    hotspot = get_user_hotspot(user)
    if not is_hotspot_expired(hotspot):
        updatedHotspot = add_extra_hotspot_properties(hotspot)
        hotspot_list.append(updatedHotspot)
    return hotspot_list


def get_user_hotspot(user):
    hotspot = Beacon.objects.filter(creator=user).latest('date_created')
    return hotspot


def invited_to_attending(beacon, user, contact):
    name = get_user_or_contact_name(user, contact)
    push_message, chat_message, avatar_url = is_going(name)
    create_hotspot_message_in_chat(beacon, chat_message, user, contact, avatar_url)
    send_hotspot_push_to_correct_profiles(beacon, push_message, message_type=MESSAGE_TYPE.HOTSPOT_JOIN)


def invited_or_going_to_here(beacon, user, contact, checkedInByUser):
    name = get_user_or_contact_name(user, contact)
    checkedInByName = get_user_or_contact_name(checkedInByUser, None)
    if user == checkedInByUser:
        push_message, chat_message, avatar_url = is_here(name)
    else:
        push_message, chat_message, avatar_url = is_here_check_in(name, checkedInByName)
    create_hotspot_message_in_chat(beacon, chat_message, user, contact, avatar_url)
    send_hotspot_push_to_correct_profiles(beacon, push_message)


def going_or_here_to_invited(beacon, user, contact, checkedOutByUser):
    name = get_user_or_contact_name(user, contact)
    checkedOutByName = get_user_or_contact_name(checkedOutByUser, None)
    if user == checkedOutByName:
        chat_message, avatar_url = has_left(name)
    else:
        chat_message, avatar_url = has_left_checked_out(name, checkedOutByName)
    create_hotspot_message_in_chat(beacon, chat_message, user, contact, avatar_url=avatar_url)


def state_change(beacon, oldState, newState, user, contact, checkedInByUser):
    if oldState == BEACON_FOLLOW_STATUS.INVITED and newState == BEACON_FOLLOW_STATUS.GOING:
        invited_to_attending(beacon, user, contact)
    elif newState == BEACON_FOLLOW_STATUS.HERE:
        invited_or_going_to_here(beacon, user, contact, checkedInByUser)
    elif oldState == BEACON_FOLLOW_STATUS.GOING or oldState == BEACON_FOLLOW_STATUS.HERE and newState == BEACON_FOLLOW_STATUS.INVITED:
        going_or_here_to_invited(beacon, user, contact, checkedInByUser)


def create_or_get_beacon_follow_user_object(user, beacon):
        if BeaconFollow.objects.filter(user=user, beacon=beacon).exists():
            return BeaconFollow.objects.filter(user=user, beacon=beacon).latest('date_created')
        # else:
        #     return BeaconFollow.create(user=user, beacon=beacon, state=BEACON_FOLLOW_STATUS.INVITED)


def create_or_get_beacon_follow_contact_object(contact, beacon):
    if BeaconFollow.objects.filter(contact=contact, beacon=beacon).exists():
        return BeaconFollow.objects.filter(contact=contact, beacon=beacon).latest('date_created')
    # else:
    #     return BeaconFollow.create(contact=contact, beacon=beacon, state=BEACON_FOLLOW_STATUS.INVITED)


def get_new_state(state):
    if state == 'Here':
        return BEACON_FOLLOW_STATUS.HERE
    elif state == 'Attending':
        return BEACON_FOLLOW_STATUS.GOING
    elif state == "Invited":
        return BEACON_FOLLOW_STATUS.INVITED
    else:
        return False


def get_user_full_name(user):
    if user.last_name == "":
        name = user.first_name
    else:
        name = "{0} {1}".format(user.first_name, user.last_name)
    return name


def send_push_to_checked_in_user(checkedInUser, checkedInByUser, beacon_id):
    checkedInByName = get_user_full_name(checkedInByUser)
    pushText = "{0} checked you in".format(checkedInByName)
    send_hotspot_message.delay(users=[checkedInUser], push_text=pushText,
                               message_type=MESSAGE_TYPE.HOTSPOT_UPDATE, beacon_id=beacon_id)


#Main functions
def mobileview_hotspot_follow(invite_id):
    beacon_invite = BeaconFollow.objects.get(pk=invite_id)
    beacon = beacon_invite.beacon
    contact = beacon_invite.contact
    beaconInvite = create_or_get_beacon_follow_contact_object(contact, beacon)
    oldState = beaconInvite.state
    newState = BEACON_FOLLOW_STATUS.GOING
    if oldState != newState:
        beaconInvite.state = newState
        beaconInvite.save()
        invited_to_attending(beacon, None, contact)


def follow_hotspot(user, data_request):
    if not ('beacon_id' in data_request and 'follow' in data_request):
        return False
    checkedInUser = None
    checkedInContact = None
    checkedInByUser = user
    beacon_id = data_request['beacon_id']
    if Beacon.objects.filter(pk=beacon_id).exists():
        beacon = Beacon.objects.get(pk=beacon_id)
        if 'user_id' in data_request:
            checkedInUser = User.objects.get(pk=data_request['user_id'])
            beaconInvite = create_or_get_beacon_follow_user_object(checkedInUser, beacon)
            if user.id != int(data_request['user_id']):
                send_push_to_checked_in_user(checkedInUser, checkedInByUser, beacon_id)
        elif 'contact_id' in data_request:
            checkedInContact = Contact.objects.get(pk=data_request['contact_id'])
            beaconInvite = create_or_get_beacon_follow_contact_object(checkedInContact, beacon)
        else:
            checkedInUser = user
            beaconInvite = create_or_get_beacon_follow_user_object(checkedInUser, beacon)

        oldState = beaconInvite.state
        newState = get_new_state(data_request['follow'])
        beaconInvite.state = newState

        if oldState != newState:
            if newState == BEACON_FOLLOW_STATUS.GOING or newState == BEACON_FOLLOW_STATUS.HERE:
                beaconInvite.checked_in_by = checkedInByUser
            state_change(beacon, oldState, newState, checkedInUser, checkedInContact, checkedInByUser)
        beaconInvite.save()
        return beacon
    else:
        return False


def get_hotspot_list(user):
    hotspot_list = []
    yesterday = datetime.now() - timedelta(days=1)
    hotspot_invites = BeaconFollow.objects.filter(user=user, beacon__cancelled=False,
                                                  beacon__time__gte=yesterday).select_related('beacon')
    for follow in hotspot_invites:
        hotspot = follow.beacon
        if not is_hotspot_expired(hotspot):
            updated_hotspot = add_extra_hotspot_properties(hotspot)
            hotspot_list.append(updated_hotspot)
    return hotspot_list