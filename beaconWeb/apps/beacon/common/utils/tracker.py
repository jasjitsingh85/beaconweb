from django.contrib.auth.models import User
from beaconWeb.apps.beacon.common.constants.view_types import VIEW_TYPE
from beaconWeb.apps.beacon.models.view_tracker import ViewTracker
from beaconWeb.apps.beacon.models.event_tracker import EventTracker
from beaconWeb.apps.beacon.models.event_status import EventStatus
from beaconWeb.apps.beacon.models.sponsored_event import SponsoredEvent
from beaconWeb.apps.beacon.models.notification_tracker import NotificationTracker
from beaconWeb.apps.beacon.common.constants.notification_types import NOTIFICATION_TYPE
from datetime import datetime, timedelta
import facebook
from beaconWeb.settings import RQ_THREAD
from django_rq import job
from django.conf import settings
from facebookads.api import FacebookAdsApi
from facebookads import objects


def track_view(user, request_data):
    if 'view_type' and 'view_id' not in request_data:
        return False
    view_type = request_data['view_type']
    view_id = request_data['view_id']
    view_tracker = ViewTracker(user=user, view_type=view_type, view_id=view_id)
    view_tracker.save()


def track_notification(recipient_user, notification_type, notification_detail=None, sending_user=None):
    notification_tracker = NotificationTracker(recipient=recipient_user, notification_type=notification_type,
                                               notification_detail=notification_detail, sender=sending_user)
    notification_tracker.save()


@job(RQ_THREAD)
def store_event_numbers():
    user = User.objects.get(username="5413359388")
    facebook_api = facebook.GraphAPI(access_token=user.profile.fb_token)
    sponsored_event = SponsoredEvent.objects.filter(active=True, start__gte=datetime.now())
    for event in sponsored_event:
        attendees = facebook_api.get_object(id=event.facebook_event_id + "/attending")
        interested = facebook_api.get_object(id=event.facebook_event_id + "/interested")
        attendee_count = get_event_count(attendees)
        interested_count = get_event_count(interested)
        # data = get_ad_data(event)
        store_event_info(event, attendee_count, interested_count)


def get_ad_data(event):
    user = User.objects.get(username="5413359388")
    access_token = "EAAKijrdivowBABFhM27DVfgH0GneI7EoS1ssKMTQRUxd7wDtH50CW5TlNlXZBQUXTJj9trJa8mcWsbOPypMVifUClhdo6FYbH8aO7ZATS35A9sidjAYUtTZAqeEayg3QcylDwL0r8UGyG9QuWuhWoKJQt0OGY71RYoLmNbgFwZDZD"
    ads_api = FacebookAdsApi.init(settings.FACEBOOK_APP_ID, settings.FACEBOOK_APP_SECRET, access_token)


def store_event_info(event, attendee_count, interested_count):
    event_tracker = EventTracker(event=event, attendee_count=attendee_count, interested_count=interested_count)
    event_tracker.save()


def get_event_count(response):
    return len(response['data'])