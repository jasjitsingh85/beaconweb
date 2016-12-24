from beaconWeb.apps.beacon.common.constants.hotbot_avatar import HOTBOT_AVATAR
from beaconWeb.common_utils import smart_format
#Helper Functions


def get_correct_friend_tense(numberOfFriends):
    if numberOfFriends == 1:
        return "friend"
    else:
        return "friends"

#Main Functions


#Invitation Messages
def set_hotspot_message(user):
    chat_message = smart_format("{0} set this Hotspot", user.first_name)
    avatar_url = HOTBOT_AVATAR.NEUTRAL
    return chat_message, avatar_url


def invite_friends_message(user, numberOfInvites):
    friend_tense = get_correct_friend_tense(numberOfInvites)
    chat_message = smart_format("{0} invited {1} {2}", user.first_name, numberOfInvites, friend_tense)
    avatar_url = HOTBOT_AVATAR.HAPPY
    return chat_message, avatar_url


#Invitation State changes
def is_going(name):
    push_message = smart_format("{0} is coming", name)
    chat_message = smart_format("{0} is coming", name)
    avatar_url = HOTBOT_AVATAR.EXCITED
    return push_message, chat_message, avatar_url


def is_here(name):
    push_message = smart_format("{0} is here", name)
    chat_message = smart_format("{0} is here", name)
    avatar_url = HOTBOT_AVATAR.EXCITED
    return push_message, chat_message, avatar_url


def is_here_check_in(name, checkedInByName):
    push_message = smart_format("{0} checked {1} in", checkedInByName, name)
    chat_message = smart_format("{0} checked {1} in", checkedInByName, name)
    avatar_url = HOTBOT_AVATAR.EXCITED
    return push_message, chat_message, avatar_url


def has_left(name):
    chat_message = smart_format("{0} has left", name)
    avatar_url = HOTBOT_AVATAR.SAD
    return chat_message, avatar_url


def has_left_checked_out(name, checkedOutByName):
    chat_message = smart_format("{0} has checked {1} out", checkedOutByName, name)
    avatar_url = HOTBOT_AVATAR.SAD
    return chat_message, avatar_url