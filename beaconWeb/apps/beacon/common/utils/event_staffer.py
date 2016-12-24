from beaconWeb.settings import RQ_THREAD
from django_rq import job
from beaconWeb.apps.beacon.models.sponsored_event import SponsoredEvent
from beaconWeb.apps.beacon.models.brand_ambassador import BrandAmbassador
from beaconWeb.apps.beacon.models.market import Market
from beaconWeb.apps.beacon.common.constants.staffer_response import STAFFER_RESPONSE
from beaconWeb.apps.beacon.common.constants.staffer_notification import STAFFER_NOTIFICATION
from beaconWeb.apps.beacon.common.constants.manager_status import MANAGER_STATUS
from beaconWeb.apps.beacon.common.common_utils import fetch_bitly_url, get_market_for_event
from django.conf import settings
from beaconWeb.common_utils import normalize_phone_number
from beaconWeb.apps.beacon.models.event_staffer import EventStaffer
from beaconWeb.apps.beacon.models.event_manager import EventManager
from beaconWeb.apps.beacon.models.staffer_notifications import StafferNotification
from beaconWeb.apps.beacon.common.common_utils import get_market_from_lat_lng
from django.db.models.signals import post_save
from django.dispatch import receiver
from beaconWeb.apps.beacon.tasks.send_sms import send_chat_sms
from beaconWeb.apps.beacon.common.constants.staffer_status import STAFFER_STATUS
from beaconWeb.geo_timezone import GeoTimeZone
import pytz
import datetime
import traceback
from beaconWeb.apps.beacon.retention.emails import send_error_email, send_marketing_email


event_manager_number = "2064601510"


@job(RQ_THREAD)
def run_event_staffing():
    send_day_before_reminder()
    send_day_of_reminder()


def get_staffers_for_this_week():
    all_staffers = []
    min_dt = datetime.datetime.now()
    max_dt = min_dt + datetime.timedelta(weeks=1)
    if SponsoredEvent.objects.filter(start__range=(min_dt, max_dt)).exists():
        events = SponsoredEvent.objects.filter(start__range=(min_dt, max_dt))
        for event in events:
            staffers = EventStaffer.objects.filter(event=event)
            all_staffers.extend(staffers)
    return all_staffers


def send_day_before_reminder():
    tomorrow = datetime.datetime.now() + datetime.timedelta(days=1)
    min_dt = datetime.datetime.combine(tomorrow, datetime.time.min)
    max_dt = datetime.datetime.combine(tomorrow, datetime.time.max)
    if SponsoredEvent.objects.filter(start__range=(min_dt, max_dt)).exists():
        events = SponsoredEvent.objects.filter(start__range=(min_dt, max_dt))
        for event in events:
            staffers = EventStaffer.objects.filter(event=event)
            for staffer in staffers:
                url = get_shortened_staffer_url(staffer)
                time = get_event_time(staffer.event)
                text = "You're scheduled to staff the event tomorrow at {0}. Make sure you arrive at {1} by {2}.\n " \
                       "Event Dashboard Link: {3}".format(staffer.event.place.name, staffer.event.place.street_address, time, url)
                send_chat_sms(text, [normalize_phone_number(staffer.manager.phone_number)])


def send_day_of_reminder():
    today = datetime.datetime.now()
    min_dt = datetime.datetime.combine(today, datetime.time.min)
    max_dt = datetime.datetime.combine(today, datetime.time.max)
    if SponsoredEvent.objects.filter(start__range=(min_dt, max_dt)).exists():
        events = SponsoredEvent.objects.filter(start__range=(min_dt, max_dt))
        for event in events:
            staffers = EventStaffer.objects.filter(event=event)
            for staffer in staffers:
                url = get_shortened_staffer_url(staffer)
                time = get_event_time(staffer.event)
                text = "You're scheduled to staff the event today at {0}. Make sure you arrive at {1} by {2}.\n " \
                       "Event Dashboard Link: {3}".format(staffer.event.place.name, staffer.event.place.street_address,
                                                          time, url)
                print text
                send_chat_sms(text, [normalize_phone_number(staffer.manager.phone_number)])


def get_shortened_staffer_url(staffer):
    shortened_url = "{0}/manager/{1}".format(settings.URL, staffer.id)
    shortened_url = fetch_bitly_url(shortened_url)
    return shortened_url


def get_event_time(event):
    latitude = event.place.latitude
    longitude = event.place.longitude
    new_timezone = GeoTimeZone().get_timezone(latitude=latitude, longitude=longitude)
    server_timezone = pytz.timezone(settings.TIME_ZONE)
    localized_time = server_timezone.localize(event.start - datetime.timedelta(minutes=30))
    updated_time = localized_time.astimezone(tz=new_timezone)
    return updated_time.strftime("%-I:%M%p")


def get_event_date(event):
    latitude = event.place.latitude
    longitude = event.place.longitude
    new_timezone = GeoTimeZone().get_timezone(latitude=latitude, longitude=longitude)
    server_timezone = pytz.timezone(settings.TIME_ZONE)
    localized_time = server_timezone.localize(event.start - datetime.timedelta(minutes=30))
    updated_time = localized_time.astimezone(tz=new_timezone)
    return updated_time.strftime("%A %B %-d")


@job(RQ_THREAD)
def check_to_send_initial_staffer_notifications():
    try:
        upcoming_events = SponsoredEvent.objects.filter(start__gte=datetime.datetime.now())
        for event in upcoming_events:
            has_primary_staffer = EventStaffer.objects.filter(event=event).filter(status=STAFFER_STATUS.PRIMARY).exists()
            has_backup_staffer = EventStaffer.objects.filter(event=event).filter(status=STAFFER_STATUS.BACKUP).exists()
            if not (has_primary_staffer or has_backup_staffer):
                market = get_market_from_lat_lng(event.place.latitude, event.place.longitude)
                texted_managers = StafferNotification.objects.filter(event=event, notification_type=STAFFER_NOTIFICATION.INITIAL).values_list('manager', flat=True)
                managers_to_text = EventManager.objects.filter(market=market).exclude(pk__in=texted_managers).exclude(status=MANAGER_STATUS.INACTIVE)
                if managers_to_text:
                    time = get_event_time(event)
                    date = get_event_date(event)
                    if not has_primary_staffer:
                        body = "Hotspot here! Would you be able to staff the event at {0} on {1} at {2}?\n\nPlease respond either 'Yes' or 'No' as soon as you can".format(event.place.name, date, time)
                        for manager in managers_to_text:
                            send_chat_sms(body, manager.phone_number, event_manager_number)
                            create_initial_staffer_notification_tracker(event, manager)
                    elif not has_backup_staffer:
                        body = "Hotspot here! Would you be able to be the back-up for the event at {0} on {1} at {2}?\n\nPlease respond either 'Yes' or 'No' as soon as you can".format(
                            event.place.name, date, time)
                        for manager in managers_to_text:
                            send_chat_sms(body, manager.phone_number, event_manager_number)
                            create_initial_staffer_notification_tracker(event, manager)
                # else:
                #     if (not has_primary_staffer):
                #         body = "{0} doesn't have a primary staffer for the event at {1} and no more managers to text".format(
                #             market.name, event.place.name)
                #         send_chat_sms(body, "5413359388", event_manager_number)
                #     if (not has_backup_staffer):
                #         body = "{0} doesn't have a backup staffer for the event at {1} and no more managers to text".format(
                #             market.name, event.place.name)
                #         send_chat_sms(body, "5413359388", event_manager_number)
    except:
        html = "Sending initial staffer notifications failed"
        traceback.print_exc()
        html = html + str(traceback.format_exc())
        send_error_email(html)


@job(RQ_THREAD)
def check_to_send_first_reminder_staffer_notifications():
    try:
        day_after_tomorrow = datetime.datetime.now() + datetime.timedelta(days=2)
        min_dt = datetime.datetime.combine(day_after_tomorrow, datetime.time.min)
        max_dt = datetime.datetime.combine(day_after_tomorrow, datetime.time.max)
        if SponsoredEvent.objects.filter(start__range=(min_dt, max_dt)).exists():
            events = SponsoredEvent.objects.filter(start__range=(min_dt, max_dt))
            count = 0
            for event in events:
                staffers = EventStaffer.objects.filter(event=event, status=STAFFER_STATUS.PRIMARY)
                for staffer in staffers:
                    url = get_shortened_staffer_url(staffer)
                    time = get_event_time(staffer.event)
                    text = "You're scheduled to staff the event day after tomorrow at {0}. Make sure you arrive at {1} by {2}. Please confirm this by responding 'Yes'".format(staffer.event.place.name, staffer.event.place.street_address, time)
                    send_chat_sms(text, normalize_phone_number(staffer.manager.phone_number), event_manager_number)
                    notification = StafferNotification(event=staffer.event, manager=staffer.manager, notification_type=STAFFER_NOTIFICATION.FIRST_REMINDER)
                    notification.save()
                    count = count + 1
            gm_sms = "{0} first reminders were sent for events in two days".format(count)
            send_chat_sms(gm_sms, "5413359388", event_manager_number)
    except:
        html = "Sending first reminder staffer notifications failed"
        traceback.print_exc()
        html = html + str(traceback.format_exc())
        send_error_email(html)


@job(RQ_THREAD)
def check_to_send_second_reminder_staffer_notifications():
    try:
        today = datetime.datetime.now()
        min_dt = datetime.datetime.combine(today, datetime.time.min)
        max_dt = datetime.datetime.combine(today, datetime.time.max)
        if SponsoredEvent.objects.filter(start__range=(min_dt, max_dt)).exists():
            events = SponsoredEvent.objects.filter(start__range=(min_dt, max_dt))
            count = 0
            for event in events:
                staffers = EventStaffer.objects.filter(event=event, status=STAFFER_STATUS.PRIMARY)
                for staffer in staffers:
                    url = get_shortened_staffer_url(staffer)
                    time = get_event_time(staffer.event)
                    text = "You're scheduled to staff the event today at {0}. Make sure you arrive at {1} by {2}. Please confirm this by responding 'Yes'".format(
                        staffer.event.place.name, staffer.event.place.street_address, time)
                    send_chat_sms(text, normalize_phone_number(staffer.manager.phone_number), event_manager_number)
                    notification = StafferNotification(event=staffer.event, manager=staffer.manager,
                                                       notification_type=STAFFER_NOTIFICATION.FIRST_REMINDER)
                    notification.save()
                    count = count + 1
            gm_sms = "{0} second reminders were sent for events today".format(count)
            send_chat_sms(gm_sms, "5413359388", event_manager_number)
    except:
        html = "Sending second reminder staffer notification failed"
        traceback.print_exc()
        html = html + str(traceback.format_exc())
        send_error_email(html)


@job(RQ_THREAD)
def check_to_send_final_reminder_staffer_notifications():
    try:
        min_dt = datetime.datetime.now()
        max_dt = datetime.datetime.now() + datetime.timedelta(hours=1)
        if SponsoredEvent.objects.filter(start__gte=min_dt, start__lte=max_dt).exists():
            events = SponsoredEvent.objects.filter(start__range=(min_dt, max_dt))
            count = 0
            for event in events:
                staffers = EventStaffer.objects.filter(event=event, status=STAFFER_STATUS.PRIMARY)
                for staffer in staffers:
                    text = "You should be on your way to the event at {0}. The address is {1}. Please confirm when you arrive by responding 'HERE'".format(
                        staffer.event.place.name, staffer.event.place.street_address)
                    send_chat_sms(text, normalize_phone_number(staffer.manager.phone_number), event_manager_number)
                    notification = StafferNotification(event=staffer.event, manager=staffer.manager,
                                                       notification_type=STAFFER_NOTIFICATION.FIRST_REMINDER)
                    notification.save()
                    count = count + 1
            gm_sms = "{0} final reminders were sent for events today".format(count)
            send_chat_sms(gm_sms, "5413359388", event_manager_number)
    except:
        html = "Sending final staffer notifications failed"
        traceback.print_exc()
        html = html + str(traceback.format_exc())
        send_error_email(html)


@job(RQ_THREAD)
def send_daily_event_staffer_email_to_general_manager():
    upcoming_events = SponsoredEvent.objects.filter(start__gte=datetime.datetime.now())
    markets = Market.objects.all()
    html = "Markets to Hire Staffers<br>"
    for market in markets:
        if EventManager.objects.filter(market=market, status=STAFFER_STATUS.PRIMARY).count() < 2:
            html = html + market.name + "<br>"
    html = html + "<br>Events without Staffing<br>"
    for event in upcoming_events:
        if not EventStaffer.objects.filter(event=event, status=STAFFER_STATUS.PRIMARY).exists():
            market = get_market_for_event(event)
            html = html + str(event.place.name) + " - " + market.name + "<br> No Primary Staffer<br><br>"
    html = html + "<br>Events with Staffing<br>"
    for event in upcoming_events:
        if EventStaffer.objects.filter(event=event, status=STAFFER_STATUS.PRIMARY).exists():
            primary = EventStaffer.objects.get(event=event, status=STAFFER_STATUS.PRIMARY)
            backup = EventStaffer.objects.filter(event=event, status=STAFFER_STATUS.BACKUP)
            market = get_market_for_event(event)
            html = html + str(event.place.name) + " - " + market.name + "<br>Primary: " + primary.manager.name + " " + str(primary.manager.phone_number) + "<br>" + "Backups: " + str(len(backup)) + "<br>"
    send_marketing_email("rachael.olsen@gethotspotapp.com", "Hotspot", ["jas@gethotspotapp.com"], "Event Staffing", "", html, "Event Staffing Daily Email")


def send_primary_confirmation_to_staffer(event_staffer):
    manager = event_staffer.manager
    event = event_staffer.event
    time = get_event_time(event)
    date = get_event_date(event)
    url = get_shortened_staffer_url(event_staffer)
    body = "You're confirmed to staff the event at {0} on {1} at {2}\n\nEvent Link:{3}".format(event.place.name, date, time, url)
    send_chat_sms(body, manager.phone_number, event_manager_number)


def send_backup_confirmation_to_staffer(event_staffer):
    manager = event_staffer.manager
    event = event_staffer.event
    time = get_event_time(event)
    date = get_event_date(event)
    url = get_shortened_staffer_url(event_staffer)
    body = "You're confirmed as a back-up for the event at {0} on {1} at {2}.\n\nEvent Link: {3}".format(event.place.name, date, time, url)
    send_chat_sms(body, manager.phone_number, event_manager_number)


def create_initial_staffer_notification_tracker(event, manager):
    notification = StafferNotification(manager=manager, event=event, notification_type=STAFFER_NOTIFICATION.INITIAL)
    notification.save()


def get_list_of_managers_to_text(managers):
    managers = EventStaffer.objects.filter(manager__in=managers, is_staffed=True).filter(Q(status=STAFFER_STATUS.PRIMARY)| Q(status=STAFFER_STATUS.BACKUP))
    return managers


def print_event_staffing():
    pass


@receiver(post_save, sender=EventStaffer)
def post_save_for_event_staffer(sender, instance, created, **kwargs):
    if created:
        try:
            if instance.status == STAFFER_STATUS.PRIMARY:
                send_primary_confirmation_to_staffer(instance)
            elif instance.status == STAFFER_STATUS.BACKUP:
                send_backup_confirmation_to_staffer(instance)
        except:
            html = "post save event staffer failed"
            send_error_email(html)


@receiver(post_save, sender=BrandAmbassador)
def post_save_for_event_staffer(sender, instance, created, **kwargs):
    if created:
        try:
            #email and text manager confirmation of promo code and link for next event
            pass
        except:
            html = "post save event staffer failed"
            send_error_email(html)
