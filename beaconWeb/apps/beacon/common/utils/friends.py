import json
from django.contrib.auth.models import User
from django.db.models import Max
from django.db.models import F
from raven.contrib.django.models import client
from beaconWeb.common_utils import normalize_phone_number
from beaconWeb.apps.beacon.common.common_utils import get_normalized_phonebook, remove_duplicate_contacts
from beaconWeb.apps.beacon.models.contact import Contact
from beaconWeb.apps.beacon.models.beacon import Beacon
from beaconWeb.apps.beacon.models.profile import Profile
from beaconWeb.apps.beacon.models.friendship import Friendship
from beaconWeb.apps.beacon.models.location import Location
from beaconWeb.apps.beacon.models.beacon_follow import BeaconFollow
from beaconWeb.apps.beacon.models.contact_group import ContactGroup
from beaconWeb.apps.beacon.models.group_member import GroupMember
from beaconWeb.apps.beacon.models.blocked_friends import BlockedFriend
from beaconWeb.apps.beacon.common.common_utils import safe_bulk_create
from django.db.models import Count
from django_rq import job
from beaconWeb.settings import RQ_THREAD
from datetime import datetime, timedelta
import heapq
import facebook
import traceback


def get_friends_and_removed_friends_list(user):
    if Location.objects.filter(user=user).exists():
        last_location = Location.objects.filter(user=user).latest('date_created')
        lat_range = [last_location.latitude - 1, last_location.latitude + 1]
        lon_range = [last_location.longitude - 1, last_location.longitude + 1]
        location_adjusted_user_ids = Location.objects.filter(latitude__range=lat_range, longitude__range=lon_range).values_list('user', flat=True)
    else:
        location_adjusted_user_ids = User.objects.all().values_list('pk', flat=True)
    friend_ids, blocked_friend_ids = get_friends(user)
    approved_friends = User.objects.filter(pk__in=location_adjusted_user_ids).filter(pk__in=friend_ids)
    blocked_friends = User.objects.filter(pk__in=location_adjusted_user_ids).filter(pk__in=blocked_friend_ids)
    return approved_friends, blocked_friends


def get_all_filtered_contacts_for_user(user):
    users_to_invite_ids, blocked_friend_ids = get_friends(user)
    additional_friends = get_friends_for_favorite_feed(user)
    additional_friends_ids = additional_friends.values_list('pk', flat=True)
    all_user_ids = set(list(users_to_invite_ids) + list(additional_friends_ids))
    final_list = [x for x in all_user_ids if x not in blocked_friend_ids]
    all_contacts = User.objects.filter(pk__in=final_list).exclude(pk=user.id)
    return all_contacts


def get_friends_for_favorite_feed(user):
    if Location.objects.filter(user=user).exists():
        last_location = Location.objects.filter(user=user).latest('date_created')
        lat_range = [last_location.latitude - 0.1, last_location.latitude + 0.1]
        lon_range = [last_location.longitude - 0.1, last_location.longitude + 0.1]
        location_adjusted_user_ids = Location.objects.filter(latitude__range=lat_range, longitude__range=lon_range).values_list('user', flat=True)
    else:
        location_adjusted_user_ids = User.objects.all().values_list('pk', flat=True)
    friend_ids = get_friends_who_invited_user(user)
    invited_friends = User.objects.filter(pk__in=location_adjusted_user_ids).filter(pk__in=friend_ids)
    return invited_friends


def get_friends_who_invited_user(user):
    friend_ids = Friendship.objects.filter(friend=user, is_blocked=False).values_list('user', flat=True)
    return friend_ids


def get_facebook_friends(user):
    users_friends = []
    if user.profile.fb_token:
        facebook_api = facebook.GraphAPI(access_token=user.profile.fb_token)
        try:
            friends = facebook_api.get_connections(id='me', connection_name='friends', limit=5000)
            friend_facebook_ids = []
            for friend in friends['data']:
                friend_facebook_ids.append(friend['id'])
            profiles = Profile.objects.filter(facebook_id__in=friend_facebook_ids)
            for profile in profiles:
                users_friends.append(profile.user.id)
        except Exception:
            traceback.print_exc()
    return users_friends


def get_friends(user):
    friend_ids = Friendship.objects.filter(user=user, is_blocked=False).values_list('friend', flat=True)
    blocked_friend_ids = Friendship.objects.filter(user=user, is_blocked=True).values_list('friend', flat=True)
    return friend_ids, blocked_friend_ids


def remove_items_in_list(original_list, items_to_remove):
    new_list = [item for item in original_list if item not in items_to_remove]
    return new_list


def toggle_blocking_of_friend(user, request_data):
    if 'user_id' not in request_data:
        return False
    friend_id = int(request_data['user_id'])
    friend = User.objects.get(pk=friend_id)
    friendship = Friendship.objects.get(user=user, friend=friend)
    friendship.is_blocked = not friendship.is_blocked
    friendship.save()
    return friendship.is_blocked


#Helper functions
def get_recent_list(user):
    recent_contact_list = []
    recent_profile_list = []

    beacon_list = list(Beacon.objects.filter(creator=user).order_by('-date_created')[:6])

    recent_list = set(BeaconFollow.objects.filter(beacon__in=beacon_list).select_related('contact', 'user'))

    for contact in recent_list:
        if contact.contact:
            recent_contact_list.append(contact.contact)
        if contact.user:
            p = Profile.objects.get(user=contact.user)
            if p:
                recent_profile_list.append(p)

    recent_contact_set = set(recent_contact_list)
    recent_profile_set = set(recent_profile_list)

    return list(recent_profile_set), list(recent_contact_set)


def convert_location_to_user_list(locationQSet):
    user_list = []
    for location in locationQSet:
        user_list.append(location.user)
    return user_list


def remove_profiles_outside_of_radius(user, normalized_phone_list):
    max_date = datetime.now()
    min_date = max_date - timedelta(weeks=52)
    if user.locations.exists():
        last_location = Location.objects.filter(user=user).latest('date_created')
        lat_range = [last_location.latitude - 0.1, last_location.latitude + 0.1]
        lon_range = [last_location.longitude - 0.1, last_location.longitude + 0.1]
        locations = Location.objects.filter(user__profile__normalized_phone__in=normalized_phone_list).annotate(latest=Max("user__locations__date_created")).filter(date_created=F("latest"))
        location_adjusted_user_ids = set(locations.filter(latitude__range=lat_range, longitude__range=lon_range, date_created__range=[min_date, max_date]).values_list('user_id', flat=True))
        valid_users = User.objects.filter(pk__in=location_adjusted_user_ids)
        # valid_users = [location.user for location in locations]
        # users_without_location = User.objects.filter(profile__normalized_phone__in=normalized_phone_list, locations=None)
        # valid_users.extend(list(users_without_location))
    else:
        valid_users = list(User.objects.filter(profile__normalized_phone__in=normalized_phone_list))
    valid_profiles = [o.profile for o in valid_users]
    return valid_profiles, valid_users


def get_contact_intersections_alternate(user, user_list):
    for userInList in user_list:
        contact_book = Contact.objects.filter(user=userInList).values_list('normalized_phone', flat=True)
        full_contact_intersection = Contact.objects.filter(user=user, normalized_phone__in=contact_book)
        contact_intersection = remove_duplicate_contacts(full_contact_intersection)


def get_contact_intersections(user, user_list):
    contact_list_counts = {}
    for userInList in user_list:
        contact_book = Contact.objects.filter(user=userInList).values_list('normalized_phone', flat=True)
        full_contact_intersection = Contact.objects.filter(user=user, normalized_phone__in=contact_book)
        contact_intersection = remove_duplicate_contacts(full_contact_intersection)
        for contact in contact_intersection:
            contact_phone = contact.normalized_phone
            if contact_phone in contact_list_counts.keys():
                contact_list_counts[contact_phone] += 1
            else:
                contact_list_counts[contact_phone] = 1
    return contact_list_counts


def get_list_of_all_hotspot_invites(user):
    beaconList = []
    beaconInvitations = BeaconFollow.objects.filter(user=user).order_by('-date_created')[:10].select_related('beacon')
    for invite in beaconInvitations:
        beaconList.append(invite.beacon)
    allHotspotInvites = BeaconFollow.objects.filter(beacon__in=beaconList).select_related('user', 'contact')
    return allHotspotInvites


def add_count_for_invitations(user, contact_list_counts, profile_queryset):
    allHotspotInvites = get_list_of_all_hotspot_invites(user)
    for invite in allHotspotInvites:
        invite_user = invite.user
        invite_contact = invite.contact
        if profile_queryset.filter(user=invite_user).exists():
            profile = profile_queryset.get(user=invite_user)
            phone = profile.normalized_phone
            if phone in contact_list_counts.keys():
                contact_list_counts[phone] += 3
            else:
                contact_list_counts[phone] = 3
        elif invite_contact:
            phone = invite_contact.normalized_phone
            if phone in contact_list_counts.keys():
                contact_list_counts[phone] += 3
            else:
                contact_list_counts[phone] = 3
    return contact_list_counts


def validate_contact(contact):
    if len(contact.normalized_phone) < 20 and len(contact.phone_number) < 20 and len(contact.name) < 50:
        return True
    else:
        return False


def contacts_from_data(user, data):
    phone_numbers = []
    for c_json in data:
        try:
            cobj = json.loads(c_json)
            phone = normalize_phone_number(cobj['phone'])
            phone_numbers.append(phone)
        except Exception:
            client.captureException()
    return Contact.objects.filter(user=user, normalized_phone__in=phone_numbers)


def create_contact_group(user, contacts, group_name):
    group = ContactGroup.objects.create(user=user, name=group_name)
    for contact in contacts:
        GroupMember.objects.create(group=group, contact=contact)
    return group


def edit_contact_group(contact_group, contacts_to_add, contacts_to_remove):
    contact_group.members.filter(contact__in=contacts_to_remove).delete()
    for contact in contacts_to_add:
        GroupMember.objects.create(group=contact_group, contact=contact)
    return contact_group


#Main functions
def store_contact_list(user, phone_list):
    new_contact_list = []
    for c_json in phone_list:
        try:
            cobj = json.loads(c_json)
            phone = cobj['phone']
            name = cobj['name']
            contact = Contact(user=user, name=name, phone_number=phone, normalized_phone=normalize_phone_number(phone))
            new_contact_list.append(contact)
        except Exception:
            client.captureException()

    stored_contact_numbers = Contact.objects.filter(user=user, normalized_phone__in=[contact.normalized_phone for contact in new_contact_list]).values_list('normalized_phone', flat=True)
    stored_contact_numbers = set(stored_contact_numbers)
    contacts_to_add = []
    for contact in new_contact_list:
        if not contact.normalized_phone in stored_contact_numbers:
            if validate_contact(contact):
                contacts_to_add.append(contact)

    if len(contacts_to_add):
        safe_bulk_create(contacts_to_add)

    update_contact_friendships(user)


def update_all_friendships(users):
    for user in users:
        update_contact_friendships(user)
        update_facebook_friendships(user)


def update_contact_friendships(user):
    contact_phone_numbers = Contact.objects.filter(user=user).values_list('normalized_phone', flat=True)
    friends_in_contacts = User.objects.filter(username__in=contact_phone_numbers)
    friendships = Friendship.objects.filter(user=user)
    print "USER: " + str(user)
    for friend in friends_in_contacts:
        if not friendships.filter(friend=friend).exists():
            Friendship.objects.create(user=user, friend=friend, is_from_contact=True)
        else:
            friendship = friendships.get(friend=friend)
            friendship.is_from_contact = True
            friendship.save()
    auto_add_reverse_friendships(user)


def auto_add_reverse_friendships(user):
    friendships = Friendship.objects.filter(user=user, is_from_contact=True)
    for friendship in friendships:
        if not Friendship.objects.filter(user=friendship.friend, friend=user).exists():
            Friendship.objects.create(user=friendship.friend, friend=user, is_auto_add=True)
        else:
            friendship = Friendship.objects.filter(user=friendship.friend, friend=user)[0]
            friendship.is_auto_add = True
            friendship.save()


def update_facebook_friendships(user):
    if user.profile.fb_token:
        facebook_api = facebook.GraphAPI(access_token=user.profile.fb_token)
        try:
            friends = facebook_api.get_connections(id='me', connection_name='friends', limit=5000)
            friend_facebook_ids = []
            for friend in friends['data']:
                friend_facebook_ids.append(friend['id'])
            profiles = Profile.objects.filter(facebook_id__in=friend_facebook_ids)
            for profile in profiles:
                add_facebook_friend(user, profile.user)
        except Exception:
            traceback.print_exc()


def add_facebook_friend(user, friend):
    if not Friendship.objects.filter(user=user, friend=friend).exists():
        Friendship.objects.create(user=user, friend=friend, is_from_facebook=True)
    else:
        friendship = Friendship.objects.get(user=user, friend=friend)
        friendship.is_from_facebook = True
        friendship.save()

    if not Friendship.objects.filter(user=friend, friend=user).exists():
        Friendship.objects.create(user=friend, friend=user, is_from_facebook=True)
    else:
        friendship = Friendship.objects.get(user=friend, friend=user)
        friendship.is_from_facebook = True
        friendship.save()

def remove_duplicate_contacts_for_user(user):
    duplicate_counts = Contact.objects.filter(user=user).values('normalized_phone').annotate(dup_count=Count('normalized_phone')).exclude(dup_count=1)
    phones = [o['normalized_phone'] for o in duplicate_counts]
    for phone in phones:
        contacts = user.contacts.filter(normalized_phone=phone)
        #remove all but the first contact
        for contact in contacts[1:]:
            contact.delete()


def get_profiles(user):
    users_normalized_phone_list = get_normalized_phonebook(user)
    all_profiles, all_users = remove_profiles_outside_of_radius(user, users_normalized_phone_list)
    # all_profiles = Profile.objects.filter(normalized_phone__in=users_normalized_phone_list)
    return all_profiles


def get_suggested_list(user, location_adjusted_profiles):
    # users_normalized_phone_list = get_normalized_phonebook(user)
    profile_queryset = Profile.objects.filter(pk__in=[o.id for o in location_adjusted_profiles])
    contact_list_counts = get_contact_intersections(user, [o.user for o in profile_queryset])
    # contact_list_counts = add_count_for_invitations(user, contact_list_counts, profile_queryset)
    # recent_profiles, recent_contacts = get_recent_list(user)
    # contact_list_counts = add_count_for_recents(user, contact_list_counts, recent_contacts)

    profiles = Profile.objects.filter(normalized_phone__in=contact_list_counts.keys())
    for profile in profiles:
        contact_list_counts[profile.normalized_phone] = 0

    contact_list_top = heapq.nlargest(20, contact_list_counts, key=contact_list_counts.get)
    suggested_contact_set = []
    suggested_contact_phonenumber_set = []
    suggested_contact_list = Contact.objects.filter(user=user, normalized_phone__in=contact_list_top)
    suggested_contact_phone_numbers = set(suggested_contact_list.values_list('normalized_phone', flat=True))
    for contact in suggested_contact_list:
        if (contact.normalized_phone in suggested_contact_phone_numbers) and (contact.normalized_phone not in suggested_contact_phonenumber_set):
            suggested_contact_phonenumber_set.append(contact.normalized_phone)
            suggested_contact_set.append(contact)
    return suggested_contact_set


def add_count_for_recents(user, contact_list_counts, recent_contacts):
    for contact in recent_contacts:
        if contact.normalized_phone in contact_list_counts.keys():
            contact_list_counts[contact.normalized_phone] += 25
        else:
            contact_list_counts[contact.normalized_phone] = 25

    return contact_list_counts


@job(RQ_THREAD)
def get_recent_and_suggested_list(user):
    recent_profile_list = []
    recent_contact_list = []
    users_normalized_phone_list = get_normalized_phonebook(user)
    users = list(User.objects.filter(profile__normalized_phone__in=users_normalized_phone_list))
    profiles = [o.profile for o in users]
    all_profiles = profiles
    suggested_profile_list = []
    suggested_contact_set = get_suggested_list(user, profiles)
    return suggested_profile_list, suggested_contact_set, recent_profile_list, recent_contact_list, all_profiles


def migrate_blocked_friends():
    blocked_friends = BlockedFriend.objects.filter(is_blocked=True)
    for blocked_friend in blocked_friends:
        print blocked_friend.user.get_full_name() + " " + blocked_friend.friend.get_full_name()
        if Friendship.objects.filter(user=blocked_friend.user, friend=blocked_friend.friend).exists():
            friendship = Friendship.objects.get(user=blocked_friend.user, friend=blocked_friend.friend)
            friendship.is_blocked = True
            friendship.save()
            print "Saved"
