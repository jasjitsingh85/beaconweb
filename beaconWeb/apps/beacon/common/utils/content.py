from beaconWeb.apps.beacon.common.constants.display_locations import *
from beaconWeb.apps.beacon.models.content_option import ContentOption
from beaconWeb.apps.beacon.classes.content_options import Content_Options


def add_enum_to_dict(enum):
    content = ContentOption.objects.filter(display_location=enum)
    return content


def get_content_options():
    content = Content_Options()
    content.friend_already_invited = add_enum_to_dict(DISPLAY_LOCATIONS.FRIEND_ALREADY_INVITED_DIALOG)
    content.invite_new_users = add_enum_to_dict(DISPLAY_LOCATIONS.INVITE_NEW_USERS)
    content.no_hotspot_content = add_enum_to_dict(DISPLAY_LOCATIONS.SET_HOTSPOT_NO_CONTENT_DIALOG)
    content.hotspot_placeholder = add_enum_to_dict(DISPLAY_LOCATIONS.SET_HOTSPOT_PLACEHOLDER)
    content.zero_hotspot = add_enum_to_dict(DISPLAY_LOCATIONS.ZERO_HOTSPOTS_MESSAGE)
    return content