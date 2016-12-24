from beaconWeb.apps.twilio_sms.models import TwilioSMS
from beaconWeb.apps.beacon.models.beacon_follow import BeaconFollow
from beaconWeb.apps.beacon.models.deal_status import DealStatus
from beaconWeb.apps.beacon.models.event_manager import EventManager
from beaconWeb.apps.beacon.models.contact_status import ContactStatus
from beaconWeb.apps.beacon.models.chat_line import ChatLine
from beaconWeb.apps.beacon.models.sms_conversation import SmsConversation
from beaconWeb.apps.beacon.models.staffer_notifications import StafferNotification
from beaconWeb.apps.beacon.models.event_staffer import EventStaffer
from beaconWeb.apps.beacon.common.constants.staffer_notification import STAFFER_NOTIFICATION
from beaconWeb.apps.beacon.common.constants.staffer_status import STAFFER_STATUS
from beaconWeb.apps.beacon.common.constants.staffer_response import STAFFER_RESPONSE
from beaconWeb.apps.beacon.common.utils.event_staffer import get_shortened_staffer_url
from beaconWeb.apps.beacon.models.contact import Contact
from beaconWeb.apps.beacon.tasks.send_sms import send_chat_sms
from django.db.models import Q
from django.contrib.auth.models import User
from beaconWeb.apps.beacon.tasks.send_sms import send_chat_sms
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


event_manager_phone = "2064601510"

def received_twilio_sms(twilio_sms):
    from_phone = normalize_phone_number(twilio_sms.from_number)
    print str(from_phone)
    chat_line_phone = normalize_phone_number(twilio_sms.to_number)
    print str(chat_line_phone)
    body = twilio_sms.body
    track_sms_received(from_phone, twilio_sms.body)
    if ChatLine.objects.filter(phone=chat_line_phone).exists():
        chat_line = ChatLine.objects.get(phone=chat_line_phone)
        from_user = User.objects.get(username=from_phone)
        if SmsConversation.objects.filter(chat_line=chat_line, active=True).filter(Q(user_one=from_user)|Q(user_two=from_user)).exists():
            print "Found SMS Conversation"
            if SmsConversation.objects.filter(user_one=from_user, chat_line=chat_line, active=True).exists():
                sms_conversation = SmsConversation.objects.get(user_one=from_user, chat_line=chat_line, active=True)
                to_phone = sms_conversation.user_two.username
                print "User One"
                send_chat_sms(body, to_phone, chat_line_phone)
            elif SmsConversation.objects.filter(user_two=from_user, chat_line=chat_line, active=True).exists():
                sms_conversation = SmsConversation.objects.get(user_two=from_user, chat_line=chat_line, active=True)
                to_phone = sms_conversation.user_one.username
                print "User Two"
                send_chat_sms(body, to_phone, chat_line_phone)


def received_twilio_sms_from_staffer(twilio_sms):
    from_phone = normalize_phone_number(twilio_sms.from_number)
    body = twilio_sms.body
    manager = EventManager.objects.get(phone_number=from_phone)
    if StafferNotification.objects.filter(manager=manager).exists():
        last_notification = StafferNotification.objects.filter(manager=manager).latest('date_created')
        print from_phone
        print body
        if last_notification.notification_type == STAFFER_NOTIFICATION.INITIAL:
            if ("yes" in body.lower()) and (last_notification.response is None):
                event = last_notification.event
                last_notification.response = STAFFER_RESPONSE.YES
                last_notification.save()
                if not EventStaffer.objects.filter(event=event).filter(status=STAFFER_STATUS.PRIMARY).exists():
                    event_staffer = EventStaffer(event=event, manager=manager, status=STAFFER_STATUS.PRIMARY)
                    event_staffer.save()
                else:
                    event_staffer = EventStaffer(event=event, manager=manager, status=STAFFER_STATUS.BACKUP)
                    event_staffer.save()
            elif ("no" in body.lower()) and (last_notification.response is None):
                last_notification.response = STAFFER_RESPONSE.NO
                last_notification.save()
            else:
                text_for_gm = "{0} in {1} ({2}) sent this: {3}".format(manager.name, manager.market, manager.phone_number, body)
                send_chat_sms(text_for_gm, "5413359388", event_manager_phone)
        elif last_notification.notification_type == STAFFER_NOTIFICATION.FIRST_REMINDER:
            if ("yes" in body.lower()) and (last_notification.response is None):
                last_notification.response = STAFFER_RESPONSE.YES
                last_notification.save()
                staffer = EventStaffer.objects.get(event=last_notification.event, manager=last_notification.manager)
                url = get_shortened_staffer_url(staffer)
                text_to_staffer = "Awesome!\n\nEvent Link: {0}".format(url)
                send_chat_sms(text_to_staffer, last_notification.manager.phone_number, event_manager_phone)
                text_to_gm = "{0} just checked in for event at {1}".format(last_notification.manager.name, last_notification.event.place.name)
                send_chat_sms(text_to_gm, "5413359388", event_manager_phone)
            else:
                text_for_gm = "{0} in {1} ({2}) sent this: {3}".format(manager.name, manager.market, manager.phone_number, body)
                send_chat_sms(text_for_gm, "5413359388", event_manager_phone)
        elif last_notification.notification_type == STAFFER_NOTIFICATION.SECOND_REMINDER:
            if ("yes" in body.lower()) and (last_notification.response is None):
                last_notification.response = STAFFER_RESPONSE.YES
                last_notification.save()
                staffer = EventStaffer.objects.get(event=last_notification.event, manager=last_notification.manager)
                url = get_shortened_staffer_url(staffer)
                text_to_staffer = "Awesome!\n\nEvent Link: {0}".format(url)
                send_chat_sms(text_to_staffer, last_notification.manager.phone_number, event_manager_phone)
                text_to_gm = "{0} just checked in for event at {1}".format(last_notification.manager.name, last_notification.event.place.name)
                send_chat_sms(text_to_gm, "5413359388", event_manager_phone)
            else:
                text_for_gm = "{0} in {1} ({2}) sent this: {3}".format(manager.name, manager.market, manager.phone_number, body)
                send_chat_sms(text_for_gm, "5413359388", event_manager_phone)
        elif last_notification.notification_type == STAFFER_NOTIFICATION.THIRD_REMINDER:
            if ("here" in body.lower()) and (last_notification.response is None):
                last_notification.response = STAFFER_RESPONSE.YES
                last_notification.save()
                staffer = EventStaffer.objects.get(event=last_notification.event, manager=last_notification.manager)
                url = get_shortened_staffer_url(staffer)
                text_to_staffer = "Awesome!\n\nEvent Link: {0}".format(url)
                send_chat_sms(text_to_staffer, last_notification.manager.phone_number, event_manager_phone)
                text_to_gm = "{0} just checked in for event at {1}".format(last_notification.manager.name,
                                                                           last_notification.event.place.name)
                send_chat_sms(text_to_gm, "5413359388", event_manager_phone)
            else:
                text_for_gm = "{0} in {1} ({2}) sent this: {3}".format(manager.name, manager.market, manager.phone_number,
                                                                       body)
                send_chat_sms(text_for_gm, "5413359388", event_manager_phone)
        else:
            text_for_gm = "Error: {0}".format(manager.name)
            send_chat_sms(text_for_gm, "5413359388", event_manager_phone)
    else:
        text_for_gm = "Error: {0}".format(manager.name)
        send_chat_sms(text_for_gm, "5413359388", event_manager_phone)


def get_user_boolean(deal_status):
    if deal_status.user is None:
        return False
    else:
        return True


def update_contact_status(deal_status, sms_response):
    if ContactStatus.objects.filter(deal_status=deal_status).exists():
        contact_status = ContactStatus.objects.filter(deal_status=deal_status)[0]
        contact_status.sms_response = sms_response
        contact_status.save()


def deal_status_for_beacon_follow(beacon_follow):
    if beacon_follow.contact:
        q = Q(contact=beacon_follow.contact)
    else:
        q = Q(user=beacon_follow.user)
    deal_statuses = DealStatus.objects.filter(q, beacon=beacon_follow.beacon)
    deal_status = None
    if deal_statuses.exists():
        deal_status = deal_statuses[0]
    return deal_status


def check_to_send_bonus(latest_beacon_follow):
    contact = latest_beacon_follow.contact
    experiment_start = datetime(2014, 10, 10)
    if contact is not None:
        contacts = Contact.objects.filter(normalized_phone=contact.normalized_phone)
        if BeaconFollow.objects.filter(contact__in=contacts, state="G", date_created__gt=experiment_start).exists():
            rsvps = len(BeaconFollow.objects.filter(contact__in=contacts, state="G", date_created__gt=experiment_start))
            if rsvps % 3 == 1:
                return True
            else:
                return False
        else:
            return False
    else:
        return False

