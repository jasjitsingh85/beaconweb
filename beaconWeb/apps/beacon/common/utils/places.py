from beaconWeb.apps.beacon.models import Deal, DealHours, Favorites, SyndicatedDeal, SyndicatedEvents, DealStatus, PlacePhotos, EventStatus
from beaconWeb.common_utils import distance_between_two_points
from beaconWeb.geo_timezone import GeoTimeZone
import datetime
from beaconWeb.apps.beacon.common.utils.deals import get_list_of_places_for_user, bitmask_for_day
from beaconWeb.apps.beacon.common.common_utils import add_presale_property
import time
from beaconWeb.apps.beacon.common.utils.friends import get_friends
from django.contrib.auth.models import User
from beaconWeb.apps.beacon.common.constants.event_status import EVENT_STATUS
from beaconWeb.apps.beacon.common.utils.friends import get_all_filtered_contacts_for_user
from beaconWeb.apps.beacon.common.utils.sponsored_events import get_sponsored_events


def add_extra_properties_to_sponsored_events(user, sponsored_events):
    user_event_statuses = EventStatus.objects.filter(user=user, status=EVENT_STATUS.GOING)
    user_contacts = get_all_filtered_contacts_for_user(user)
    for sponsored_event in sponsored_events:
        friend_event_statuses = EventStatus.objects.filter(user__in=user_contacts, event=sponsored_event, status=EVENT_STATUS.GOING).distinct('user')
        all_event_statuses = EventStatus.objects.filter(event=sponsored_event, status=EVENT_STATUS.GOING).distinct('user')
        if EventStatus.objects.filter(user=user, event=sponsored_event, refund_authorization__isnull=True).exists():
            user_event_status = EventStatus.objects.filter(user=user, event=sponsored_event, refund_authorization__isnull=True)[0]
            sponsored_event.event_status = user_event_status
            sponsored_event.status_message = get_status_message(user, sponsored_event, all_event_statuses, True)
        else:
            sponsored_event.event_status = None
            sponsored_event.status_message = get_status_message(user, sponsored_event, all_event_statuses, False)

        sponsored_event.place.photos = get_photos_for_venue(sponsored_event.place)
        sponsored_event.is_sold_out = is_event_sold_out(all_event_statuses)
        sponsored_event.social_message = get_social_message(user, sponsored_event, user_contacts, friend_event_statuses)
        sponsored_event = add_presale_property(sponsored_event)

    return sponsored_events


def get_photos_for_venue(deal_place):
    photos = PlacePhotos.objects.filter(place=deal_place, image_date__gte=datetime.datetime.now()-datetime.timedelta(weeks=12)).order_by('-like_count')[:10].values_list('source_image_url', flat=True)
    return photos


def is_event_sold_out(event_statuses):
    if len(event_statuses) > 0:
        if len(event_statuses) > event_statuses[0].event.capacity:
            return True
        else:
            return False
    else:
        return False


def get_social_message(user, sponsored_event, user_contacts, event_statuses):
    number_of_friends_going = len(event_statuses)
    if number_of_friends_going == 0:
        number_going = EventStatus.objects.filter(event=sponsored_event, status=EVENT_STATUS.GOING).distinct('user').count()
        number_redeemed = EventStatus.objects.filter(event=sponsored_event, status=EVENT_STATUS.REDEEMED).distinct('user').count()
        total_number = number_going + number_redeemed
        if total_number == 0:
            # return "No one is going"
            return ""
        elif total_number <= 50:
            # return "1 person is going"
            return ""
        else:
            return str(total_number) + " people are going"
    elif number_of_friends_going == 1:
        return event_statuses[0].user.get_full_name() + " is going"
    elif number_of_friends_going > 1:
        # random_friend = event_statuses.order_by('?')[0].user.get_full_name()
        return str(number_of_friends_going) + " friends are going"


def get_status_message(user, sponsored_event, event_statuses, is_reserved):
    if is_reserved:
        return "Reserved"
    elif len(event_statuses) >= sponsored_event.capacity:
        return "Sold Out"
    else:
        return ""


def nearby_venues(user, latitude, longitude, radius):
    sponsored_events = get_sponsored_events(user, latitude, longitude)
    sponsored_events = add_extra_properties_to_sponsored_events(user, sponsored_events)
    t0 = time.time()
    places = get_list_of_places_for_user(user, latitude, longitude)
    t1 = time.time()
    # today_deals = DealHours.objects.filter(days_active=weekday_bit).values_list('deal', flat=True)
    place_ids_with_deals = Deal.objects.filter(in_app_payment=True, active=True).values_list('place', flat=True)
    filtered_places = []
    for place in places:
        place.distance = distance_between_two_points(latitude, longitude, place.latitude, place.longitude)
    t2 = time.time()
    places.sort(key=lambda x: x.distance)

    timezone = GeoTimeZone().get_timezone(latitude=latitude, longitude=longitude)
    now = datetime.datetime.now(tz=timezone)
    time_in_seconds = (now.hour * 3600) + (now.minute * 60) + now.second
    bitmask = bitmask_for_day((now.weekday() + 2) % 7)

    happy_hours = SyndicatedDeal.objects.filter(days_active=bitmask, place__in=places, end__gte=time_in_seconds, in_review=False).select_related('place')
    places_with_happy_hours = happy_hours.values_list('place', flat=True)

    events = SyndicatedEvents.objects.filter(place__in=places, start__gte=datetime.datetime.now()-datetime.timedelta(hours=6), start__lte=datetime.datetime.now()+datetime.timedelta(weeks=1)).order_by('start')
    places_with_events = events.values_list('place', flat=True)

    active_place_ids = list(places_with_events) + list(places_with_happy_hours)

    deal_count = 0
    for place in places:
        place_id = place.id
        if place_id in place_ids_with_deals and deal_count < 25:
            filtered_places.append(place)
            deal_count += 1
        elif (place.distance < radius) and (place_id in active_place_ids):
            filtered_places.append(place)

    #This is a repeated to improve speed...
    happy_hours = SyndicatedDeal.objects.filter(days_active=bitmask, place__in=filtered_places, end__gte=time_in_seconds, in_review=False).order_by('start').select_related('place')
    events = SyndicatedEvents.objects.filter(place__in=filtered_places, start__gte=datetime.datetime.now()-datetime.timedelta(hours=6), start__lte=datetime.datetime.now()+datetime.timedelta(weeks=1)).order_by('start')

    t3 = time.time()
    filtered_places = add_extras_to_places(user, filtered_places, latitude, longitude, happy_hours, events)
    t4 = time.time()
    deals, non_deals = add_active_deals_to_places(user, filtered_places)
    t5 = time.time()
    # places_in_radius = add_reward_info_to_places(user, places_in_radius)
    deals.sort(key=lambda x: x.distance)
    non_deals.sort(key=lambda x: x.distance)
    t6 = time.time()

    return sponsored_events, deals, non_deals


def add_extras_to_places(user, places, latitude, longitude, happy_hours, events):
    followed_places = Favorites.objects.filter(user=user, active=True).values_list('place_id', flat=True)

    # places_with_deals = Deal.objects.filter(active=True, in_app_payment=True, place_id__in=[x.pk for x in places], deal_type="DT").values_list('place', flat=True)

    filtered_places = []
    places_with_happy_hours = happy_hours.values_list('place', flat=True)
    places_with_events = events.values_list('place', flat=True)
    photos = PlacePhotos.objects.filter(place__in=places)
    # # active_places = list(places_with_events) + list(places_with_happy_hours) + list(places_with_deals)
    # active_place_ids = list(places_with_events) + list(places_with_happy_hours)
    # active_places = DealPlace.objects.filter(pk__in=active_place_ids)
    print str(len(places))
    t0 = time.time()
    for place in places:
        place_id = place.id
        place.photos = get_photos(photos, place)
        if place_id in places_with_happy_hours:
            place.happy_hour = happy_hours.filter(place=place).order_by('start')[0]
        else:
            place.happy_hour = None

        if place_id in places_with_events:
            place.events = events.filter(place=place)
        else:
            place.events = None

        if place_id in followed_places:
            place.is_followed = True
        else:
            place.is_followed = False
        filtered_places.append(place)
    t1 = time.time()
    print str(t1-t0)
    return filtered_places


def get_photos(photos, deal_place):
    photos = photos.filter(place=deal_place, image_date__gte=datetime.datetime.now()-datetime.timedelta(weeks=12)).order_by('-like_count')[:10].values_list('source_image_url', flat=True)
    return photos


def add_active_deals_to_places(user, places):
    active_deals = Deal.objects.filter(active=True, in_app_payment=True, place_id__in=[x.pk for x in places], deal_type="DT")
    active_deal_statuses = DealStatus.objects.filter(deal__in=active_deals)
    active_deals_ids = active_deals.values_list('place', flat=True)
    if len(active_deals) > 0:
        timezone = GeoTimeZone().get_timezone(latitude=active_deals[0].place.latitude, longitude=active_deals[0].place.longitude)
        now = datetime.datetime.now(tz=timezone)
    else:
        now = datetime.datetime.now()
    # now = datetime.datetime.now()
    weekday = (now.weekday() + 1) % 7
    weekday_bit = [DealHours.days_active.Sunday, DealHours.days_active.Monday, DealHours.days_active.Tuesday,
                   DealHours.days_active.Wednesday, DealHours.days_active.Thursday, DealHours.days_active.Friday,
                   DealHours.days_active.Saturday][weekday]
    now_in_seconds = 60*60*now.hour + 60*now.minute + now.second
    deal_hours = DealHours.objects.filter(deal__in=active_deals)
    user_reward_items = user.profile.number_of_reward_items
    deals = []
    non_deals = []
    for place in places:
        place_id = place.id
        if place_id in active_deals_ids:
            deals_qs = active_deals.filter(place=place)
            for deal in deals_qs:
                if deal_hours.filter(deal=deal, days_active=weekday_bit, end__gte=now_in_seconds).exists():
                    place.deal = deal
                    place.deal.total_check_ins = active_deal_statuses.filter(deal=deal).count()
                    if place.deal.reward_eligibility and user_reward_items > 0:
                        place.deal.is_reward_item = True
                    else:
                        place.deal.is_reward_item = False
                    deals.append(place)
        else:
            place.deal = None
            # place.is_reward_item = False
            non_deals.append(place)
    return deals, non_deals


# def add_reward_info_to_places(user, places):
#     user_reward_items = user.profile.number_of_reward_items
#     for place in places:
#         if place.deal.reward_eligibility and user_reward_items > 0:
#             place.is_reward_item = True
#         else:
#             place.is_reward_item = False
#     return places