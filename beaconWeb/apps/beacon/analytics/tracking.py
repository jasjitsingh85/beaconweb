from mixpanel import Mixpanel
from django.conf import settings
from beaconWeb.settings import RQ_THREAD
from django_rq import job

mp = Mixpanel(settings.MIXPANEL_TOKEN)


def track_sms_sent(contact_phone, message, isUser):
    distinct_id = contact_phone
    event_name = 'sms_invite_sent'
    properties = {"message": message, "isUser": isUser}
    track_event_async(distinct_id, event_name, properties)


def track_sms_received(sender_phone, message_body):
    distinct_id = sender_phone
    event_name = 'sms_received'
    properties = {"body": message_body}
    track_event_async(distinct_id, event_name, properties)


def track_coupon_sms_sent(recipient_phone):
    distinct_id = recipient_phone
    event_name = 'coupon_sms_sent'
    properties = {}
    track_event_async(distinct_id, event_name, properties)


def track_bonus_sms_sent(recipient_phone):
    distinct_id = recipient_phone
    event_name = 'bonus_sms_sent'
    properties = {}
    track_event_async(distinct_id, event_name, properties)

def track_event_async(distinct_id, event_name, properties={}, meta={}):
    if settings.ENVIRONMENT and settings.ENVIRONMENT == 'Production':
        track_event.delay(distinct_id, event_name, properties, meta)


@job(RQ_THREAD)
def track_event(distinct_id, event_name, properties={}, meta={}):
    if settings.ENVIRONMENT and settings.ENVIRONMENT == 'Production':
        mp.track(distinct_id, event_name, properties, meta)