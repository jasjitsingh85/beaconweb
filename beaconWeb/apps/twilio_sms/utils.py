from twilio.rest import TwilioRestClient
from django.conf import settings
from beaconWeb.apps.twilio_sms.models import TwilioSMS
from datetime import datetime, timedelta
from beaconWeb.common_utils import safe_bulk_create

twilio_client = TwilioRestClient(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)


def sync_sms():
    try:
        after = TwilioSMS.objects.latest('date_created_twilio').date_created_twilio - timedelta(seconds=60*5)
    except:
        after = datetime.min
    messages = twilio_client.sms.messages.list(after=after, to=settings.TWILIO_PHONE)
    sids = [message.sid for message in messages]
    existing = TwilioSMS.objects.filter(twilio_sid__in=sids).values_list('twilio_sid', flat=True)
    new = []
    for message in messages:
        if message.sid not in existing:
            sms = TwilioSMS(twilio_sid=message.sid, body=message.body, status=message.status,
                            direction=message.direction, to_number=message.to, from_number=message.from_,
                            date_created_twilio=message.date_created, date_sent_twilio=message.date_sent)
            new.append(sms)

    safe_bulk_create(new)
    return new

