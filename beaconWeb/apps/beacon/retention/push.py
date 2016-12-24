from beaconWeb.apps.beacon.models import DealStatus, Deal, Beacon, Rewards, RewardItem, ContactStatus, Contact, Location, Friendship, EventStatus
from beaconWeb.apps.beacon.common.constants.reward_types import REWARD_TYPES
from beaconWeb.apps.beacon.common.constants.event_status import EVENT_STATUS
from beaconWeb.apps.beacon.common.constants.reward_values import REWARD_VALUES
from beaconWeb.apps.beacon.common.utils.deals import get_list_of_places_for_user
from beaconWeb.apps.beacon.analytics.analytics import get_user_within_distance
from beaconWeb.apps.beacon.tasks.send_sms import send_hotspot_push
from django.contrib.auth.models import User
from datetime import datetime, timedelta
from beaconWeb.apps.beacon.common.utils.tracker import track_notification
from beaconWeb.apps.beacon.common.constants.notification_types import NOTIFICATION_TYPE


def free_drink_retention_push(min_date=datetime.now()-timedelta(weeks=1), max_date=datetime.now()):
    users_in_seattle = get_user_within_distance(47.667759, -122.312766, 20)
    active_users = Location.objects.filter(date_created__gte=min_date, date_created__lt=max_date, user__in=users_in_seattle).values_list('user', flat=True).distinct()
    inactive_users_with_free_drinks_ids = RewardItem.objects.filter(isRedeemed=False, reward_type=REWARD_TYPES.DRINK, user__in=users_in_seattle).exclude(user_id__in=active_users).values_list("user_id", flat=True)
    inactive_users_with_free_drinks = User.objects.filter(pk__in=inactive_users_with_free_drinks_ids)
    message = "You still have a free drink waiting on Hotspot. Redeem it soon!"
    for user in inactive_users_with_free_drinks:
        send_hotspot_push([user], message)
        track_notification(user, NOTIFICATION_TYPE.FREE_DRINK_REMINDER_PUSH)


def send_push_reminder(event):
    users_with_friends, users_without_friends = separate_users_for_event_push(event)
    send_friends_message(users_with_friends, event)
    send_regular_push_message(users_without_friends, event)


def send_friends_message(users_with_friends, event):
    for user in users_with_friends:
        friend_ids = Friendship.objects.filter(user=user).values_list('friend', flat=True)
        event_statuses = EventStatus.objects.filter(user_id__in=friend_ids, status=EVENT_STATUS.GOING)
        if len(event_statuses) > 1:
            message = "{0} friends are going to the open bar tomorrow at {1}. The presale ends today - make sure to reserve your ticket soon!".replace("{0}", str(len(event_statuses))).replace("{1}", event.place.name)
        else:
            message = "{0} friend is going to the open bar tomorrow at {1}. The presale ends today - make sure to reserve your ticket soon!".replace("{0}", str(len(event_statuses))).replace("{1}", event.place.name)
        send_hotspot_push([user], message)


def send_regular_push_message(users_without_friends, event):
    for user in users_without_friends:
        message = "The presale ends today for the open bar tomorrow at {0}. Make sure to reserve your ticket soon!".replace("{0}", event.place.name)
        send_hotspot_push([user], message)


def separate_users_for_event_push(sponsored_event):
    lat = sponsored_event.place.latitude
    lng = sponsored_event.place.longitude
    reserved_user_ids = EventStatus.objects.filter(event=sponsored_event, status=EVENT_STATUS.GOING).values_list('user', flat=True)
    users = get_user_within_distance(lat, lng, 40)
    filtered_users = users.exclude(pk__in=reserved_user_ids)
    users_with_friends_ids = Friendship.objects.filter(user_id__in=reserved_user_ids).values_list('friend', flat=True)
    users_with_friends = filtered_users.filter(pk__in=users_with_friends_ids)
    users_without_friends = filtered_users.exclude(pk__in=users_with_friends_ids)
    return users_with_friends, users_without_friends
