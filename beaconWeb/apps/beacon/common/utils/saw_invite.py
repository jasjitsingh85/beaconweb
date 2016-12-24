from beaconWeb.apps.beacon.models import Beacon
from beaconWeb.apps.beacon.models.beacon_follow import BeaconFollow
from beaconWeb.apps.beacon.tasks.send_sms import send_hotspot_message
from beaconWeb.common_utils import smart_format
from beaconWeb.apps.beacon.common.constants.message_type import MESSAGE_TYPE


def check_or_update_saw_invite(beacon_follow):
    print beacon_follow.saw_invite
    if beacon_follow.saw_invite is False:
        print "Was false, will now be made true"
        beacon_follow.saw_invite = True
        beacon_follow.save()
        if beacon_follow.contact:
            name = beacon_follow.contact.name
        else:
            name = beacon_follow.user.first_name
        message = smart_format("{0} read your invitation", name)
        if beacon_follow.invited_by is not None:
            send_hotspot_message.delay(users=[beacon_follow.invited_by], push_text=message,
                                       message_type=MESSAGE_TYPE.HOTSPOT_UPDATE, beacon_id=beacon_follow.beacon.id)
    else:
        print "Was already true, no change"


#main functions
def mobileview_saw_invite(follow_id):
    beacon_follow = BeaconFollow.objects.get(pk=follow_id)
    check_or_update_saw_invite(beacon_follow)


def saw_invite(user, request_data):
    if 'beacon_id' in request_data:
        beacon_id = int(request_data['beacon_id'])
        if BeaconFollow.objects.filter(user=user, beacon_id=beacon_id).exists():
            beacon_follow = BeaconFollow.objects.filter(user=user, beacon_id=beacon_id).latest('date_created')
            print beacon_follow.saw_invite
            first_view = not beacon_follow.saw_invite
            print first_view
            check_or_update_saw_invite(beacon_follow)
            return first_view
        else:
            print "beacon follow object does not exist"
    else:
        print "beacon_id not in request_data"