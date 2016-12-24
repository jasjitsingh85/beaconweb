from beaconWeb.apps.beacon.models import EventStatus, SponsoredEvent, PlacePhotos
from django.contrib.auth.models import User
from beaconWeb.apps.beacon.common.utils.deals import notify_friends_of_user_for_event
from beaconWeb.apps.beacon.common.utils.places import get_social_message, get_status_message
from beaconWeb.apps.beacon.common.utils.friends import get_all_filtered_contacts_for_user
from beaconWeb.apps.beacon.common.constants.event_status import EVENT_STATUS
from datetime import datetime, timedelta
from beaconWeb.apps.beacon.common.common_utils import add_presale_property
from beaconWeb.apps.beacon.common.utils.payments import charge_user_for_event
from beaconWeb.geo_timezone import GeoTimeZone
from beaconWeb.apps.beacon.retention.emails import send_app_order_confirmation


def get_event(user, event_id):
    sponsored_event = SponsoredEvent.objects.get(pk=event_id)
    # user_event_statuses = EventStatus.objects.filter(user=user, status=EVENT_STATUS.GOING)
    user_contacts = get_all_filtered_contacts_for_user(user)
    all_event_statuses = EventStatus.objects.filter(event=sponsored_event, status=EVENT_STATUS.GOING).distinct('user')
    event_statuses = EventStatus.objects.filter(user__in=user_contacts, event=sponsored_event, status=EVENT_STATUS.GOING).distinct('user')
    if EventStatus.objects.filter(event=sponsored_event, user=user).exists():
        event_status = EventStatus.objects.filter(event=sponsored_event, user=user)[0]
        sponsored_event.event_status = event_status
    else:
        sponsored_event.event_status = None
    sponsored_event.status_message = get_status_message(user, sponsored_event, all_event_statuses, True)
    sponsored_event.social_message = get_social_message(user, sponsored_event, user_contacts, event_statuses)
    sponsored_event.is_sold_out = is_event_sold_out(all_event_statuses)
    sponsored_event.place.photos = get_photos_for_venue(sponsored_event.place)
    sponsored_event = add_presale_property(sponsored_event)
    return sponsored_event


def get_photos_for_venue(deal_place):
    photos = PlacePhotos.objects.filter(place=deal_place, image_date__gte=datetime.now()-timedelta(weeks=12)).order_by('-like_count')[:10].values_list('source_image_url', flat=True)
    return photos


def has_capacity(request_data):
    if 'event_id' not in request_data:
        return False
    event = SponsoredEvent.objects.get(pk=int(request_data['event_id']))
    all_event_statuses = EventStatus.objects.filter(event=event, status=EVENT_STATUS.GOING).distinct('user')
    return not is_event_sold_out(all_event_statuses)


def get_tip_from_request(request_data):
    if 'tip_amount' in request_data:
        return float(request_data['tip_amount'])
    else:
        return 0.0


def reserve_ticket(user, request_data):
    if 'is_public' and 'event_id' not in request_data:
        return False
    event = SponsoredEvent.objects.get(pk=int(request_data['event_id']))
    is_public = bool(int(request_data['is_public']))
    tip = get_tip_from_request(request_data)
    event_status = get_event_status_and_check_to_charge_user(user, event, EVENT_STATUS.GOING, is_public, tip)

    if event_status:
        user_contacts = get_all_filtered_contacts_for_user(user)
        all_event_statuses = EventStatus.objects.filter(event=event, status=EVENT_STATUS.GOING).distinct('user')
        event_statuses = EventStatus.objects.filter(user__in=user_contacts, event=event, status=EVENT_STATUS.GOING).distinct('user')
        event.social_message = get_social_message(user, event, user_contacts, event_statuses)
        event.status_message = get_status_message(user, event, all_event_statuses, True)
        event.is_sold_out = is_event_sold_out(all_event_statuses)
        event.event_status = event_status
        event.place.photos = get_photos_for_venue(event.place)
        event = add_presale_property(event)
        send_app_order_confirmation(event_status)

        if is_public:
            notify_friends_of_user_for_event.delay(event_status)
    else:
        event = False

    return event


def save_tip_to_event_status(event_status, tip):
    event_status.tip_amount = tip
    event_status.save()


def get_event_status_and_check_to_charge_user(user, event, status, public=False, tip=0.0):
    # if EventStatus.objects.filter(user=user, event=event).exists():
    #     event_status = EventStatus.objects.get(user=user, event=event)
    #     if status == EVENT_STATUS.GOING and event_status.status != EVENT_STATUS.GOING:
    #         save_tip_to_event_status(event_status, tip)
    #         event_status = charge_user_for_event(user, event_status)
    #         if event_status:
    #             event_status.status = EVENT_STATUS.GOING
    #     else:
    #         if event_status.status == EVENT_STATUS.INTERESTED:
    #             event_status.status = EVENT_STATUS.NO_SELECTION
    #         else:
    #             event_status.status = EVENT_STATUS.INTERESTED
    #     event_status.save()
    # else:
    if EventStatus.objects.filter(user=user, event=event, refund_authorization__isnull=True).exists():
        event_status = EventStatus.objects.filter(user=user, event=event, refund_authorization__isnull=True)[0]
    else:
        event_status = EventStatus(user=user, event=event, status=status, public=public, tip_amount=tip)
        event_status.save()
    if status == EVENT_STATUS.GOING:
        event_status = charge_user_for_event(user, event_status)
    return event_status


def toggle_interested(user, request_data):
    if 'event_id' not in request_data:
        return False
    event = SponsoredEvent.objects.get(pk=int(request_data['event_id']))
    event_status = get_event_status_and_check_to_charge_user(user, event, EVENT_STATUS.INTERESTED)

    user_contacts = get_all_filtered_contacts_for_user(user)
    all_event_statuses = EventStatus.objects.filter(event=event, status=EVENT_STATUS.GOING).distinct('user')
    event_statuses = EventStatus.objects.filter(user__in=user_contacts, event=event, status=EVENT_STATUS.GOING).distinct('user')
    event.social_message = get_social_message(user, event, user_contacts, event_statuses)
    event.status_message = get_status_message(user, event, all_event_statuses, True)
    event.is_sold_out = is_event_sold_out(all_event_statuses)
    event.event_status = event_status
    event.place.photos = get_photos_for_venue(event.place)
    event = add_presale_property(event)

    return event


def is_event_sold_out(event_statuses):
    if len(event_statuses) > 0:
        if len(event_statuses) >= event_statuses[0].event.capacity:
            return True
        else:
            return False
    else:
        return False


def redeem_ticket(user, request_data):
    event_status_id = int(request_data['event_status_id'])
    event_status = EventStatus.objects.get(pk=event_status_id)
    event_status.status = EVENT_STATUS.REDEEMED
    event_status.save()
    event = event_status.event

    user_contacts = get_all_filtered_contacts_for_user(user)
    all_event_statuses = EventStatus.objects.filter(event=event, status=EVENT_STATUS.GOING).distinct('user')
    event_statuses = EventStatus.objects.filter(user__in=user_contacts, event=event, status=EVENT_STATUS.GOING).distinct('user')
    event.social_message = get_social_message(user, event, user_contacts, event_statuses)
    event.status_message = get_status_message(user, event, all_event_statuses, True)
    event.is_sold_out = is_event_sold_out(all_event_statuses)
    event.place.photos = get_photos_for_venue(event.place)
    event.event_status = event_status
    event = add_presale_property(event)

    return event


def check_event_time(request_data):
    event_status_id = int(request_data['event_status_id'])
    event_status = EventStatus.objects.get(pk=event_status_id)

    # latitude = event_status.event.place.latitude
    # longitude = event_status.event.place.longitude
    # timezone = GeoTimeZone().get_timezone(latitude=latitude, longitude=longitude)
    # now_with_timezone = datetime.now(tz=timezone)
    event_start = event_status.event.start

    if datetime.now() > event_start - timedelta(minutes=30):
        return True
    else:
        return False
