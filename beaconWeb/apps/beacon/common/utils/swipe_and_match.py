from beaconWeb.apps.beacon.models.sponsored_event import SponsoredEvent
from beaconWeb.apps.beacon.models.dating_profile import DatingProfile
from beaconWeb.apps.beacon.models.event_status import EventStatus
from beaconWeb.apps.beacon.common.constants.event_status import EVENT_STATUS
from beaconWeb.apps.beacon.models.profile import Profile
from beaconWeb.apps.beacon.models.dating_match import DatingMatch
from beaconWeb.apps.beacon.models.sms_conversation import SmsConversation
from beaconWeb.apps.beacon.tasks.send_sms import send_chat_sms
from beaconWeb.apps.beacon.models.chat_line import ChatLine
from beaconWeb.apps.beacon.tasks.send_sms import send_hotspot_push
from datetime import datetime, timedelta
from django.contrib.auth.models import User
from beaconWeb.settings import RQ_THREAD
from django_rq import job
from django.db.models import Q


def get_dating_profile(user):
    if DatingProfile.objects.filter(dating_profile=user.profile).exists():
        user_dating_profile = DatingProfile.objects.get(dating_profile=user.profile)
        return [user_dating_profile]
    else:
        return []


def get_dating_queue_from_request(user, request_data):
    if 'event_id' not in request_data:
        return False
    event_id = int(request_data['event_id'])
    if DatingProfile.objects.filter(dating_profile=user.profile).exists():
        dating_profiles = get_dating_queue(user, event_id)
        return dating_profiles
    else:
        return []


def get_dating_queue(user, event_id, dating_profile=None):
    excluded_dating_profiles = DatingProfile.objects.filter(image_url__contains="no_profile.png").values_list('pk', flat=True)
    user_dating_profile = DatingProfile.objects.get(dating_profile=user.profile)
    already_swiped_profile_ids_to_exclude = DatingMatch.objects.filter(event_id=event_id, dating_profile_selector=user_dating_profile).values_list('dating_profile_selectee', flat=True)
    profile_ids_to_exclude = DatingProfile.objects.filter(pk__in=already_swiped_profile_ids_to_exclude).values_list('dating_profile', flat=True)
    event = SponsoredEvent.objects.get(pk=event_id)
    event_attendees = EventStatus.objects.filter(event=event).exclude(status=EVENT_STATUS.INTERESTED).exclude(status=EVENT_STATUS.NO_SELECTION).values_list('user_id', flat=True)
    profile_ids = Profile.objects.filter(user_id__in=event_attendees).exclude(user_id=user.id).values_list('pk', flat=True)
    dating_profiles = DatingProfile.objects.filter(dating_profile_id__in=profile_ids, user_gender=user_dating_profile.preference, preference=user_dating_profile.user_gender).exclude(dating_profile_id__in=profile_ids_to_exclude).exclude(pk__in=excluded_dating_profiles)
    return dating_profiles


def save_dating_profile(user, request_data):
    if 'user_gender' and 'user_preference' and 'image_url' not in request_data:
        return False
    user_gender = request_data['user_gender']
    user_preference = request_data['user_preference']
    image_url = request_data['image_url']
    # event_id = request_data['event_id']
    if DatingProfile.objects.filter(dating_profile=user.profile).exists():
        dating_profile = DatingProfile.objects.get(dating_profile=user.profile)
        dating_profile.user_gender = user_gender
        dating_profile.preference = user_preference
        dating_profile.image_url = image_url
    else:
        dating_profile = DatingProfile(dating_profile=user.profile, user_gender=user_gender, preference=user_preference, image_url=image_url)
    dating_profile.save()
    return [dating_profile]


def save_match_selection(user, request_data):
    if 'dating_profile_id' and 'is_selected' and 'event_id' not in request_data:
        return False
    dating_profile_selector = DatingProfile.objects.get(dating_profile=user.profile)
    dating_profile_selectee = DatingProfile.objects.get(pk=request_data['dating_profile_id'])
    is_selected = int(request_data['is_selected'])
    print "IS SELECTED: + " + str(is_selected)
    event_id = request_data['event_id']
    event = SponsoredEvent.objects.get(pk=event_id)
    if DatingMatch.objects.filter(dating_profile_selector=dating_profile_selector, dating_profile_selectee=dating_profile_selectee, event=event).exists():
        dating_match = DatingMatch.objects.get(dating_profile_selector=dating_profile_selector, dating_profile_selectee=dating_profile_selectee, event=event)
        dating_match.is_selected = is_selected
    else:
        dating_match = DatingMatch(dating_profile_selector=dating_profile_selector, dating_profile_selectee=dating_profile_selectee, is_selected=is_selected, event=event)
    dating_match.save()
    if is_selected:
        if DatingMatch.objects.filter(dating_profile_selector=dating_profile_selectee, dating_profile_selectee=dating_profile_selector, event=event, is_selected=True).exists():
            current_user = dating_profile_selector.dating_profile.user
            other_user = dating_profile_selectee.dating_profile.user
            message = "You matched with {0} for the event at {1}".replace("{0}", current_user.get_full_name()).replace("{1}", event.place.name)
            send_hotspot_push([other_user], message)
            try:
                create_sms_thread(current_user, other_user, event)
            except:
                # send_error_report_email("Chat Line Failed", [])
                print "SMS Thread Failed to Create"
            return [dating_profile_selectee]
        elif DatingMatch.objects.filter(dating_profile_selector=dating_profile_selectee, dating_profile_selectee=dating_profile_selector, event=event, is_selected=False).exists():
            return []
        else:
            user = dating_profile_selectee.dating_profile.user
            message = "Someone who's also going to the event at {0} just liked you on 'Swipe & Match'".replace("{0}", event.place.name)
            send_hotspot_push([user], message)
            return []
    else:
        return []


def get_matches(user, request_data):
    if 'event_id' not in request_data:
        return False
    event_id = request_data['event_id']
    event = SponsoredEvent.objects.get(pk=event_id)
    if DatingProfile.objects.filter(dating_profile=user.profile).exists():
        user_dating_profile = DatingProfile.objects.get(dating_profile=user.profile)
        user_selection_ids = DatingMatch.objects.filter(dating_profile_selector=user_dating_profile, event=event, is_selected=True).values_list('dating_profile_selectee', flat=True)
        matched_dating_profile_ids = DatingMatch.objects.filter(dating_profile_selector_id__in=user_selection_ids, dating_profile_selectee= user_dating_profile, event=event, is_selected=True).values_list('dating_profile_selector', flat=True)
        dating_profiles = DatingProfile.objects.filter(pk__in=matched_dating_profile_ids)
        return dating_profiles
    else:
        return []


@job(RQ_THREAD)
def check_for_dating_queue():
    events = SponsoredEvent.objects.filter(end__gte=datetime.now())
    dating_profile_ids = DatingProfile.objects.all().values_list('dating_profile', flat=True)
    user_ids = Profile.objects.filter(pk__in=dating_profile_ids).values_list('user', flat=True)
    filtered_event_statuses = EventStatus.objects.filter(user_id__in=user_ids, event__in=events, status=EVENT_STATUS.GOING)
    for event_status in filtered_event_statuses:
        user = event_status.user
        event = event_status.event
        dating_queue = get_dating_queue(user, event.id)
        if len(dating_queue) > 0:
            message = "You have new people to swipe through who are going to the event at {0}!".replace("{0}", event.place.name)
            send_hotspot_push([user], message)


def create_sms_thread(user_one, user_two, event):
    chat_line = get_chat_line(user_one, user_two)
    sms_conversation = SmsConversation(user_one=user_one, user_two=user_two, event=event, chat_line=chat_line)
    sms_conversation.save()
    send_initial_sms(sms_conversation)


def get_chat_line(user_one, user_two):
    open_chat_lines = SmsConversation.objects.filter(active=True).filter(Q(user_one=user_one) | Q(user_two=user_one) | Q(user_one=user_two) | Q(user_two=user_two)).values_list('chat_line')
    chat_line = ChatLine.objects.exclude(pk__in=open_chat_lines).order_by('?')[0]
    return chat_line


def send_initial_sms(sms_conversation):
    user_one = sms_conversation.user_one
    user_two = sms_conversation.user_two
    event = sms_conversation.event
    chat_line = sms_conversation.chat_line
    message_for_user_one = get_message_text(user_two, event)
    message_for_user_two = get_message_text(user_one, event)
    send_chat_sms.delay(message_for_user_one, user_one.profile.normalized_phone, chat_line.phone)
    send_chat_sms.delay(message_for_user_two, user_two.profile.normalized_phone, chat_line.phone)


def get_message_text(user, event):
    message = "You matched with {0} who is also going to the event at {1}. You can swap messages with {2} over this temporary number till the end of the event!".format(user.get_full_name(), event.place.name, user.get_full_name())
    return message
