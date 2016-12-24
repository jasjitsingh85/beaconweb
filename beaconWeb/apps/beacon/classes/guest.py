from beaconWeb.apps.beacon.models.beacon_follow import BeaconFollow
from beaconWeb.apps.beacon.common.constants.beacon_status_values import BEACON_FOLLOW_STATUS
class Guest(object):

    def __init__(self, profile, contact, status):
        self.profile = profile
        self.contact = contact
        self.status = status

    def __init__(self, beacon_follow):
        profile = None
        if beacon_follow.user:
            profile = beacon_follow.user.profile
        self.profile = profile
        self.contact = beacon_follow.contact
        status_map = {BEACON_FOLLOW_STATUS.GOING: "going",
                      BEACON_FOLLOW_STATUS.HERE: "here",
                      BEACON_FOLLOW_STATUS.INVITED: "invited",
                      BEACON_FOLLOW_STATUS.DECLINED: "invited"}
        self.status = status_map[beacon_follow.state]
