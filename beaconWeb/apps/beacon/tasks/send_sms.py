from beaconWeb.settings import RQ_THREAD
from django.contrib.auth.models import User
from ios_notifications.models import Device
from ios_notifications.models import APNService
from ios_notifications.models import Notification
from beaconWeb.apps.beacon.models.profile import Profile
from beaconWeb.apps.push_notifications.utils import send_push_notification_to_users
from twilio.rest import TwilioRestClient
from django.conf import settings
from django_rq import job
from beaconWeb.apps.beacon.analytics.tracking import track_sms_sent
from beaconWeb.gsm0338 import is_gsm, remove_non_gsm
from beaconWeb.common_utils import smart_format
from raven.contrib.django.models import client as raven_client
from time import sleep
import re


@job(RQ_THREAD)
def send_push_to_wakeup_users(users, beacon_id=None):
    print 'sending push to wakeup'
    extras = None
    if beacon_id:
        extras = {"beacon": beacon_id}
    send_push_notification_to_users(users, content_available=True, extras=extras)

@job(RQ_THREAD)
def send_hotspot_deal_invitations(users=None, contacts=None, user_sms_text=None, contact_sms_text=None):
    print 'sending message'
    user_sms_numbers = []
    contact_sms_numbers = []
    if users and len(users):
        user_sms_numbers = list(User.objects.filter(pk__in=[o.pk for o in users]).values_list('profile__normalized_phone', flat=True))

    if contacts and len(contacts):
        contact_sms_numbers.extend([o.normalized_phone for o in contacts])

    send_sms(user_sms_text, user_sms_numbers)
    send_sms(contact_sms_text, contact_sms_numbers)

@job(RQ_THREAD)
def send_hotspot_message(users=None, push_text=None, contacts=None, sms_text=None, message_type=None, beacon_id=None,
                         recommendation_id=None, image_url=None, silent=False):

    print "User List: " + str(users)
    print "Push Text: " + str(push_text)
    print "Contact List: " + str(contacts)
    print "SMS Text: " + str(sms_text)
    print "Message Type: " + str(message_type)
    print "Beacon ID: " + str(beacon_id)
    print "Recommendation ID: " + str(recommendation_id)
    print "Image URL: " + str(image_url)

    if users and len(users):
        if silent:
            send_silent_hotspot_push(users, push_text, message_type, beacon_id, recommendation_id)
        else:
            send_hotspot_push(users, push_text, message_type, beacon_id, recommendation_id)

    sms_numbers = []
    if users and len(users):
        sms_numbers = list(User.objects.filter(pk__in=[o.pk for o in users],
                                        android_devices=None,
                                        ios_devices=None).values_list('profile__normalized_phone', flat=True))
        send_sms(sms_text, sms_numbers, image_url)

    if contacts and len(contacts):
        sms_numbers.extend([o.normalized_phone for o in contacts])
        sms_text = sms_text + "\n\nBONUS: Hotspot will pay for your first drink!"
        send_sms(sms_text, sms_numbers, image_url)
        # bonus_message = "BONUS: Hotspot will pay for your first drink!"
        # send_sms(bonus_message, sms_numbers, image_url)


@job(RQ_THREAD)
def send_silent_hotspot_push(users, push_text, message_type=None, beacon_id=None, recommendation_id=None):
    extras = {}
    if message_type:
        extras['type'] = message_type
    if beacon_id:
        extras['beacon'] = beacon_id
    if recommendation_id:
        extras['rec'] = recommendation_id
    send_push_notification_to_users(users, message=push_text, badge=1, sound=None, extras=extras)


@job(RQ_THREAD)
def send_hotspot_push(users, push_text, message_type=None, beacon_id=None, recommendation_id=None, sponsored_event_id=None):
    extras = {}
    if message_type:
        extras['type'] = message_type
    if beacon_id:
        extras['beacon'] = beacon_id
    if recommendation_id:
        extras['rec'] = recommendation_id
    if sponsored_event_id:
        extras['sponsored_event'] = sponsored_event_id
    send_push_notification_to_users(users, message=push_text, badge=1, sound='default', extras=extras)


@job(RQ_THREAD)
def send_individualized_sms(contact_dict, profile_dict):
    for dict_item in contact_dict:
        message = dict_item['message']
        contact_phone = [dict_item['contact_phone']]
        track_sms_sent(contact_phone, message, isUser=False)
        send_sms(message, contact_phone)

    for dict_item in profile_dict:
        message = dict_item['message']
        profile_phone = [dict_item['profile_phone']]
        track_sms_sent(contact_phone, message, isUser=True)
        send_sms(message, profile_phone)


@job(RQ_THREAD)
def send_sms_in_background(text_body, phone_list, image_url=None):
    send_sms(text_body, phone_list, image_url)


def send_sms(text_body, phone_list, image_url=None):
    twilio_client = TwilioRestClient(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
    for phone in phone_list:
        phone = "+1" + phone
        try:
            gsm = is_gsm(text_body)
            if not gsm:
                raven_client.captureException()
                #max length for non gsm twilio sms is much shorter so remove non gsm
                text_body = remove_non_gsm(text_body)

            if image_url is not None:
                twilio_client.messages.create(body=text_body, to=phone, from_=settings.TWILIO_PHONE, media_url=image_url)
            else:
                if len(text_body) <= 160:
                    twilio_client.messages.create(body=text_body, to=phone, from_=settings.TWILIO_PHONE)
                else:
                    messages = split_message(text_body)
                    for m in messages:
                        twilio_client.messages.create(body=m, to=phone, from_=settings.TWILIO_PHONE)
                        sleep(2)
        except Exception:
            raven_client.captureException()
            pass


@job(RQ_THREAD)
def send_chat_sms(text_body, to_phone, from_phone):
    twilio_client = TwilioRestClient(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
    to_phone = "+1" + to_phone
    from_phone = "+1" + from_phone
    try:
        gsm = is_gsm(text_body)
        if not gsm:
            raven_client.captureException()
            #max length for non gsm twilio sms is much shorter so remove non gsm
            text_body = remove_non_gsm(text_body)

        if len(text_body) <= 160:
            twilio_client.messages.create(body=text_body, to=to_phone, from_=from_phone)
        else:
            messages = split_message(text_body)
            for m in messages:
                twilio_client.messages.create(body=m, to=to_phone, from_=from_phone)
                sleep(2)
    except Exception:
        raven_client.captureException()
        pass


def split_message(message):
#    twilio max length is 160
    #split at a new line if possible
    new_lines = [m.start() for m in re.finditer('\n', message)]
    split = []
    if len(new_lines):
        last_new_line = max(new_lines)
        message1 = message[:last_new_line]
        message1 = message1.strip('\n')
        split.append(message1)
        message2 = message[last_new_line+1:]
        message2 = message2.strip('\n')
        split.append(message2)
    else:
        split.append(message)
    return split




