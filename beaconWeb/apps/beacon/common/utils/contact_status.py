from beaconWeb.apps.twilio_sms.models import TwilioSMS
from beaconWeb.apps.beacon.models.beacon_follow import BeaconFollow
from beaconWeb.apps.beacon.models.deal_status import DealStatus
from beaconWeb.apps.beacon.models.contact_status import ContactStatus
from beaconWeb.apps.beacon.models.contact import Contact
from django.db.models import Q
from beaconWeb.common_utils import normalize_phone_number
from django.core.exceptions import ObjectDoesNotExist
from beaconWeb.apps.beacon.common.utils.saw_invite import check_or_update_saw_invite
from beaconWeb.apps.beacon.common.utils.hotspot_follow import invited_to_attending
from datetime import datetime, timedelta
from beaconWeb.apps.beacon.common.constants.beacon_status_values import BEACON_FOLLOW_STATUS
from beaconWeb.common_utils import smart_format
from beaconWeb.apps.beacon.tasks.send_sms import send_sms
from beaconWeb.apps.beacon.analytics.tracking import track_sms_received, track_bonus_sms_sent
from beaconWeb.apps.beacon.common.utils.hotspot import hotspot_webview_url, deal_webview_url
from beaconWeb.apps.beacon.common.constants.contact_status import CONTACT_STATUS


def update_contact_status(data):
    if "deal_status" not in data:
        return False
    contact_status = ContactStatus.objects.get(deal_status_id=int(data["deal_status"]))
    contact_status.link_clicked = True
    contact_status.save()


def update_contact_status_for_referred_phone(user, request_data):
    phone_number_list = request_data.getlist('contact_array[]')
    for phone_number in phone_number_list:
        contact_status = ContactStatus(referring_user=user, referred_phone_number=phone_number)
        contact_status.save()