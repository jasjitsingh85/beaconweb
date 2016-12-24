from beaconWeb.apps.beacon.models.deal_place import DealPlace
from beaconWeb.apps.beacon.models.deal import Deal
from beaconWeb.apps.beacon.models.deal_hours import DealHours
from beaconWeb.apps.beacon.models.notification_tracker import NotificationTracker
from beaconWeb.common_utils import distance_between_two_points
from beaconWeb.geo_timezone import GeoTimeZone
from beaconWeb.apps.beacon.common.constants.notification_types import NOTIFICATION_TYPE
from beaconWeb.apps.beacon.common.utils.places import add_active_deals_to_places
from beaconWeb.apps.beacon.tasks.send_sms import send_hotspot_push
from beaconWeb.apps.beacon.common.utils.tracker import track_notification
import datetime
from beaconWeb.apps.beacon.common.utils.deals import get_list_of_places_for_user, bitmask_for_day


def check_to_send_notification(user, location):
    latitude = location.latitude
    longitude = location.longitude
    places = get_list_of_places_for_user(user, location.latitude, location.longitude)
    deals = Deal.objects.filter(in_app_payment=True, active=True, place__in=places)

    # timezone = GeoTimeZone().get_timezone(latitude=latitude, longitude=longitude)
    # now = datetime.datetime.now(tz=timezone)
    now = datetime.datetime.now()
    weekday = (now.weekday() + 1) % 7
    weekday_bit = [DealHours.days_active.Sunday, DealHours.days_active.Monday, DealHours.days_active.Tuesday,
                   DealHours.days_active.Wednesday, DealHours.days_active.Thursday, DealHours.days_active.Friday,
                   DealHours.days_active.Saturday][weekday]
    now_in_seconds = 60*60*now.hour + 60*now.minute + now.second
    deal_hours = DealHours.objects.filter(deal__in=deals)

    if not notification_sent_that_day(user) and is_appropriate_time(now_in_seconds):
        filtered_deals = []
        for deal in deals:
            deal.distance = distance_between_two_points(latitude, longitude, deal.place.latitude, deal.place.longitude)
            if deal.distance < .5:
                filtered_deals.append(deal)
        filtered_deals.sort(key=lambda x: x.distance)

        for deal in filtered_deals:
            if deal_hours.filter(deal=deal, days_active=weekday_bit, end__gte=now_in_seconds).exists():
                if check_and_send_notification(user, deal):
                    return True


def is_appropriate_time(now_in_seconds):
    if now_in_seconds > 64800:
    # if now_in_seconds > 0:
        return True
    else:
        return False


def notification_sent_that_day(user):
    if NotificationTracker.objects.filter(recipient=user, date_created__gte=datetime.datetime.now()-datetime.timedelta(days=1), notification_type=NOTIFICATION_TYPE.BACKGROUND_NOTIFICATION).exists():
        return True
    else:
        return False


def check_and_send_notification(user, deal):
    time_cutoff = datetime.datetime.now() - datetime.timedelta(weeks=2)
    if NotificationTracker.objects.filter(recipient=user, date_created__gte=time_cutoff, notification_type=NOTIFICATION_TYPE.BACKGROUND_NOTIFICATION, notification_detail=deal.id).exists():
        return False
    else:
        send_background_deal_notification(user, deal)
        return True


def send_background_deal_notification(user, deal):
    message = "Nearby Offer: Get a {0} for ${1} at {2}".replace("{0}", deal.item_name.lower()).replace("{1}", str(int(deal.item_price))).replace("{2}", deal.place.name)
    send_hotspot_push([user], message)
    track_notification(user, NOTIFICATION_TYPE.BACKGROUND_NOTIFICATION, deal.id)
