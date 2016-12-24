from beaconWeb.apps.beacon.models.emails import Emails
from beaconWeb.apps.beacon.common.constants.email_submission import EMAIL_SUBMISSION
from beaconWeb.apps.beacon.models.sponsored_event import SponsoredEvent
from beaconWeb.apps.beacon.common.common_utils import get_market_for_event


def store_email(request_data):
    if 'email' and 'event_id' not in request_data:
        return False
    email = request_data['email']
    event_id = int(request_data['event_id'])
    event = SponsoredEvent.objects.get(pk=event_id)
    market = get_market_for_event(event)
    email = Emails(email=email, market=market, type=EMAIL_SUBMISSION.MODAL)
    email.save()
