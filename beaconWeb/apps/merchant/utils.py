from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from beaconWeb.apps.beacon.models.deal import Deal
from beaconWeb.apps.beacon.models.deal_place import DealPlace
from beaconWeb.apps.beacon.models.deal_hours import DealHours
from beaconWeb.apps.beacon.models.profile import Profile
from beaconWeb.apps.beacon.analytics.analytics import get_user_within_distance
from datetime import datetime, timedelta
from beaconWeb.apps.beacon.common.constants.user_type import USER_TYPE
from beaconWeb.apps.beacon.common.constants.deal_type import DEAL_TYPE
from rest_framework.authtoken.models import Token


def login_merchant_user(request_data):
    if 'email' and 'password' not in request_data:
        print "Email and password is not in request"
        return False
    user = authenticate(username=request_data['email'], password=request_data['password'])
    if user is not None:
        place = user.profile.deal_place
        default_deal, recurring_deal = get_merchant_deals(place)
        return user.profile.token, default_deal, recurring_deal
    else:
        print "User could not be authenticated"
        return None, None, None


def get_merchant_deals(place):
    default_deal = Deal.objects.filter(place=place, active=True, deal_type=DEAL_TYPE.DEFAULT)
    recurring_deal = Deal.objects.filter(place=place, active=True, deal_type=DEAL_TYPE.RECURRING)
    return default_deal, recurring_deal

def deactivate_deal(request_data):
    if 'deal_id' not in request_data:
        return False
    deal_id = int(request_data['deal_id'])
    deal = Deal.objects.get(pk=deal_id)
    deal.active = False
    deal.save()
    return get_merchant_deals(deal.place)

def update_deal(request_data):
    if ('deal_id' and 'deal_type') not in request_data:
        return False
    deal_type = request_data['deal_type']
    if deal_type == DEAL_TYPE.DEFAULT or deal_type == DEAL_TYPE.RECURRING:
        return update_default_or_recurring_deal(request_data)
    elif deal_type == DEAL_TYPE.EVENT:
        return update_event(request_data)
    else:
        return False


def update_default_or_recurring_deal(request_data):
    deal_id = int(request_data['deal_id'])
    deal = Deal.objects.get(pk=deal_id)
    if 'deal_title' in request_data:
        deal.deal_description_short = request_data['title']
        deal.deal_type = request_data['deal_type']
        deal.invite_requirement = int(request_data['invite_requirement'])
        deal.additional_info = request_data['additional_info']
        deal.invite_prompt = request_data['invite_prompt']
        # times = request_data['times']
        place_id = int(request_data['place_id'])
        place = DealPlace.objects.get(pk=place_id)
        deal.place = place
        invite_string = get_invite_string(deal.invite_requirement)
        deal_description = "Text {0} - {1}".format(invite_string, request_data['description'])
        # notification = "Text {0} and {1} at {2}".format(invite_string, uncapitalize(deal.deal_description_short), place.name)
        deal.deal_description = deal_description
        # deal.notification_text = notification
        deal.save()
        update_deal_hours(deal, request_data['day'], request_data['start_time'], request_data['end_time'])
    else:
        deal.active = False
        deal.save()
    return get_merchant_deals(deal.place)


def update_deal_hours(deal, day, start, end):
    DealHours.objects.filter(deal=deal).delete()
    add_deal_hours_to_deal(deal, int(day), int(start), int(end))


def add_deal_hours_to_deal(deal, day, start, end):
    weekday_bit = get_weekday_bit(day)
    DealHours.objects.create(deal=deal, days_active=weekday_bit, start=start, end=end)
    if end > 86400:
        next_day_seconds = end - 86400
        next_day_weekday_bit = get_weekday_bit((day + 1) % 7)
        add_deal_hours_to_deal(deal, next_day_weekday_bit, 0, next_day_seconds)


def update_event(request_data):
    return True


def add_deal(request_data):
    if ('deal_type' and 'title' and 'invite_requirement' and 'additional_info' and 'invite_prompt' and "times" and 'place_id') not in request_data:
        return False
    deal_type = request_data['deal_type']
    if deal_type == DEAL_TYPE.DEFAULT or deal_type == DEAL_TYPE.RECURRING:
        return add_default_or_recurring_deal(request_data)
    elif deal_type == DEAL_TYPE.EVENT:
        return add_event(request_data)
    else:
        return False


def add_default_or_recurring_deal(request_data):
    title = request_data['title']
    deal_type = request_data['deal_type']
    invite_requirement = int(request_data['invite_requirement'])
    additional_info = request_data['additional_info']
    text_message = request_data['invite_prompt']
    place_id = int(request_data['place_id'])
    place = DealPlace.objects.get(pk=place_id)
    invite_string = get_invite_string(invite_requirement)
    deal_description = "Text {0} - {1}".format(invite_string, title)
    notification = "Text {0} and {1} at {2}".format(invite_string, uncapitalize(title), place.name)
    deal = Deal.objects.create(deal_description_short=title, deal_description=deal_description, invite_requirement=invite_requirement, place=place,
                               additional_info=additional_info, invite_prompt=text_message, active=True, deal_type=deal_type,
                               notification_text=notification)
    add_deal_hours_to_deal(deal, int(request_data['day']), int(request_data['start_time']), int(request_data['end_time']))
    return get_merchant_deals(place)


def add_event(request_data):
    title = request_data['title']
    invite_requirement = int(request_data['invite_requirement'])
    additional_info = request_data['additional_info']
    text_message = request_data['invite_prompt']
    times = request_data['times']
    place_id = int(request_data['place_id'])
    place = DealPlace.objects.get(pk=place_id)
    invite_string = get_invite_string(invite_requirement)
    deal_description = "Text {0} - {1}".format(invite_string, title)
    notification = "Text {0} and {1}".format(invite_string, uncapitalize(deal_description))
    deal = Deal.objects.create(deal_description_short=title, deal_description=deal_description, invite_requirement=invite_requirement, place=place,
                               additional_info=additional_info, invite_prompt=text_message, active=True, deal_type=DEAL_TYPE.EVENT,
                               notification_text=notification)
    add_event_time_to_deal(times, deal)
    return deal


def add_times_to_deal(times, deal):
    return True


def add_event_time_to_deal(times, deal):
    return True


def uncapitalize(s):
    return s[:1].lower() + s[1:]


def get_invite_string(min_invites):
    if min_invites == 1:
        return "{0} friend".format(min_invites)
    else:
        return "{0} friends".format(min_invites)


def get_weekday_bit(weekday_int):
    weekday = weekday_int % 7
    weekday_bit = [DealHours.days_active.Sunday, DealHours.days_active.Monday, DealHours.days_active.Tuesday,
                   DealHours.days_active.Wednesday, DealHours.days_active.Thursday, DealHours.days_active.Friday,
                   DealHours.days_active.Saturday][weekday]
    return weekday_bit


def create_merchant_user(email, password, place_id):
    place = DealPlace.objects.get(pk=place_id)
    user = User.objects.create_user(username=email, email=email, first_name=" ", last_name=" ", password=password)
    Token.objects.create(user=user)
    profile = Profile.objects.create(deal_place=place, user_type=USER_TYPE.MERCHANT, user=user)
    return profile


def change_password(user, request_data):
    if "old_password" and "new_password" not in request_data:
        return False
    if user.check_password(request_data['old_password']):
        user.set_password(request_data['new_password'])
        user.save()
        return True
    else:
        return False