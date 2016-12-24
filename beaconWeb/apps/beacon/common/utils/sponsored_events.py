from datetime import datetime, timedelta
from beaconWeb.geo_timezone import GeoTimeZone
from beaconWeb.apps.beacon.models.sponsored_event import SponsoredEvent
from beaconWeb.apps.beacon.models.event_status import EventStatus
from beaconWeb.apps.beacon.models.deal_place import DealPlace
from beaconWeb.apps.beacon.common.constants.event_status import EVENT_STATUS
from beaconWeb.apps.beacon.tasks.send_sms import send_hotspot_push, send_chat_sms
from django.db.models.signals import post_save
from beaconWeb.apps.beacon.common.common_utils import get_market_from_lat_lng, get_market_for_event
from django.conf import settings
from beaconWeb.apps.beacon.common.constants.staffer_notification import STAFFER_NOTIFICATION
from beaconWeb.apps.beacon.common.constants.manager_status import MANAGER_STATUS
import pytz
import urllib2
import traceback
from beaconWeb.apps.beacon.models.event_manager import EventManager
from beaconWeb.apps.beacon.models.event_staffer import EventStaffer
from beaconWeb.apps.beacon.models.staffer_notifications import StafferNotification
from django.contrib.auth.models import User
import json
from django.dispatch import receiver
from beaconWeb.settings import RQ_THREAD
from django_rq import job
from beaconWeb.apps.beacon.retention.emails import send_error_email

event_manager_number = "2064601510"


def get_sponsored_events(user, latitude, longitude):
    # timezone = GeoTimeZone().get_timezone(latitude=latitude, longitude=longitude)
    # now = datetime.now(tz=timezone)
    now = datetime.now()
    eight_weeks_from_now = now + timedelta(weeks=8)

    lat_range = [latitude-1, latitude+1]
    lng_range = [longitude-1, longitude+1]
    places = list(DealPlace.objects.filter(latitude__range=lat_range, longitude__range=lng_range, closed=False))

    sponsored_event_qs = SponsoredEvent.objects.filter(active=True, end__gte=now, place__in=places)
    sponsored_events = list(sponsored_event_qs)
    sponsored_events.sort(key=lambda x: x.start)

    return sponsored_events


def sendbird_api(url, params):
    req = urllib2.Request(url)
    req.add_header('Content-Type', 'application/json, charset=utf8')
    try:
        response = urllib2.urlopen(req, json.dumps(params))
    except:
        return {'error': True, 'message': 'Connection failed.'}
    if response.getcode() / 100 != 2:
        print response.read()
        return {'error': True, 'message': 'Connection failed.'}
    return json.loads(response.read())


def create_and_get_channel_url(sponsored_event):
    url = 'https://api.sendbird.com/channel/create'
    channel_url = str(sponsored_event.id)
    params = {
        "auth": '61b08a439ac553ce793ac5a9264eee697045a896',
        "channel_url": channel_url,
        "name": 'string',
        "cover_url": 'string',
        "data": 'string',
    }
    return sendbird_api(url, params)['channel_url']


def send_broadcast_message(message, sponsored_event):
    send_message_to_channel(message, sponsored_event)
    send_push_notifications_to_event_attendees(message, sponsored_event)


def send_push_notifications_to_event_attendees(message, sponsored_event):
    event_attendee_ids = EventStatus.objects.filter(status="R", event=sponsored_event).values_list('user', flat=True)
    users = User.objects.filter(pk__in=event_attendee_ids)
    for user in users:
        send_hotspot_push([user], message, None, None, None, sponsored_event.id)


def send_message_to_channel(message, sponsored_event):
    url = 'https://api.sendbird.com/channel/send'
    params = {
        "auth": '61b08a439ac553ce793ac5a9264eee697045a896',
        "channel_url": sponsored_event.chat_channel_url,
        "id": '1',
        "message": message,
    }
    sendbird_api(url, params)


def send_welcome_message_to_channel(sponsored_event):
    welcome_message = "Thanks for reserving a ticket to the open bar event at {0}! You can use this room to chat with other people going to this event. If you're single, make sure to check out 'Swipe & Match' to meet cool people at the event!".replace("{0}", sponsored_event.place.name)
    url = 'https://api.sendbird.com/channel/send'
    params = {
        "auth": '61b08a439ac553ce793ac5a9264eee697045a896',
        "channel_url": sponsored_event.chat_channel_url,
        "id": '1',
        "message": welcome_message,
    }
    sendbird_api(url, params)


def create_channel_and_add_to_sponsored_event(sponsored_event):
    channel_url = create_and_get_channel_url(sponsored_event)
    sponsored_event.chat_channel_url = channel_url
    sponsored_event.save()
    send_welcome_message_to_channel(sponsored_event)


@job(RQ_THREAD)
def event_chron_job():
    check_if_thirty_minutes_left()
    send_welcome_push()
    send_arrival_push()



def check_if_thirty_minutes_left():
    pass


def send_welcome_push():
    event_statuses = EventStatus.objects.filter(welcome_message_sent=False)
    for status in event_statuses:
        if (status.status == EVENT_STATUS.REDEEMED):
            welcome_message = "Welcome to the event! If you wanna mingle, check out 'Swipe & Match' to meet people at the event!"
            send_hotspot_push([status.user], welcome_message, "EventChat", None, None, status.event.id)
            status.arrival_message_sent = True
            status.save()
        else:
            welcome_message = "Thanks for the reservation! If you wanna mingle, check out 'Swipe & Match' to meet people at the event!"
            send_hotspot_push([status.user], welcome_message, "EventChat", None, None, status.event.id)
        status.welcome_message_sent = True
        status.save()


def send_arrival_push():
    event_statuses = EventStatus.objects.filter(arrival_message_sent=False, status=EVENT_STATUS.REDEEMED)
    for status in event_statuses:
        welcome_message = "Welcome to the event! If you wanna mingle, check out 'Swipe & Match' to meet people at the event!"
        send_hotspot_push([status.user], welcome_message, "EventChat", None, None, status.event.id)
        status.arrival_message_sent = True
        status.save()


@receiver(post_save, sender=SponsoredEvent)
def post_save_for_sponsored_events(sender, instance, created, **kwargs):
    if created:
        create_channel_and_add_to_sponsored_event(instance)
        send_post_save_notifications_to_staffer(instance)
        add_market_to_sponsored_event(instance)


def add_market_to_sponsored_event(event):
    market = get_market_for_event(event)
    event.market = market
    event.save()

def send_post_save_notifications_to_staffer(event):
    try:
        market = get_market_from_lat_lng(event.place.latitude, event.place.longitude)
        managers_to_text = EventManager.objects.filter(market=market, status=MANAGER_STATUS.PRIMARY)
        time = get_event_time(event)
        date = get_event_date(event)
        body = "Hotspot here! Tickets just went live for an event at {0} on {1} at {2}. Would you be able to staff it?\n\nPlease respond either 'Yes' or 'No' as soon as you can".format(event.place.name, date, time)
        for manager in managers_to_text:
            create_initial_staffer_notification_tracker(event, manager)
            send_chat_sms(body, manager.phone_number, event_manager_number)
    except:
        html = "Sending post save notifications to staffer failed"
        traceback.print_exc()
        send_error_email(html)


# def get_list_of_managers_to_text(managers):
#     managers = EventManager.objects.filter()
#     return managers


def create_initial_staffer_notification_tracker(event, manager):
    notification = StafferNotification(manager=manager, event=event, notification_type=STAFFER_NOTIFICATION.INITIAL)
    notification.save()


def get_event_time(event):
    latitude = event.place.latitude
    longitude = event.place.longitude
    new_timezone = GeoTimeZone().get_timezone(latitude=latitude, longitude=longitude)
    server_timezone = pytz.timezone(settings.TIME_ZONE)
    localized_time = server_timezone.localize(event.start - timedelta(minutes=30))
    updated_time = localized_time.astimezone(tz=new_timezone)
    return updated_time.strftime("%-I:%M%p")


def get_event_date(event):
    latitude = event.place.latitude
    longitude = event.place.longitude
    new_timezone = GeoTimeZone().get_timezone(latitude=latitude, longitude=longitude)
    server_timezone = pytz.timezone(settings.TIME_ZONE)
    localized_time = server_timezone.localize(event.start - timedelta(minutes=30))
    updated_time = localized_time.astimezone(tz=new_timezone)
    return updated_time.strftime("%A %B %-d")




