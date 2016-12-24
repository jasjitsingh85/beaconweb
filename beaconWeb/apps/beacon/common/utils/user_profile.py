from django.contrib.auth.models import User
from beaconWeb.apps.beacon.models.profile import Profile
from beaconWeb.apps.beacon.models.contact import Contact
from beaconWeb.apps.beacon.models.beacon_follow import BeaconFollow
from beaconWeb.apps.beacon.models.deal_status import DealStatus
from beaconWeb.apps.beacon.models.promo import Promo
from beaconWeb.apps.beacon.common.common_utils import send_activation_code
from beaconWeb.common_utils import normalize_phone_number
from beaconWeb.apps.beacon.tasks.send_sms import send_sms
from beaconWeb.apps.beacon.common.utils.friends import update_facebook_friendships
from datetime import datetime, timedelta
from django.conf import settings
from beaconWeb.apps.beacon.common.utils.rewards import check_if_user_was_referred, check_promo_code
from beaconWeb.apps.beacon.analytics.tracking import track_coupon_sms_sent
import requests
from beaconWeb.apps.beacon.common.utils.login import send_push_that_friend_joined
from beaconWeb.apps.beacon.retention.emails import send_welcome_email
from beaconWeb.apps.beacon.data.facebook_scraper import update_facebook_id_and_name
from random import randint
import facebook


#Helper functions
def get_contact_with_phone(phone):
    normalizedPhone = normalize_phone_number(phone)
    if Contact.objects.filter(normalized_phone=normalizedPhone).exists():
        return list(Contact.objects.filter(normalized_phone=normalizedPhone))
    else:
        return []


def add_device(device_token):
    addDeviceURL = "{0}/ios-notifications/device/".format(settings.URL)
    addDevicePayload = {"token": str(device_token), "service": settings.APNS_SERVICE_ID}
    addDevice = requests.post(addDeviceURL, data=addDevicePayload)
    print addDevice.status_code
    return addDevice.status_code


def add_user_to_device(user, device):
    addUserURL = "{0}/ios-notifications/device/{1}/{2}/".format(settings.URL, device, settings.APNS_SERVICE_ID)
    print addUserURL
    addUserPayload = {"users": user.id}
    print addUserPayload
    addUser = requests.put(addUserURL, data=addUserPayload)
    if addUser.status_code == 200:
        return "User successfully added"
    else:
        return "User not added to device"


#Main functions
def create_user(user_data):
    if not ('first_name' and 'last_name' and 'email' and 'phone_number' in user_data):
        return False

    user = User.objects.create_user(username=user_data['phone_number'], password=" ",
                                    first_name=user_data['first_name'], last_name=user_data['last_name'],
                                    email=user_data['email'])
    user.save()
    print "User created"
    normalizedPhone = normalize_phone_number(user_data['phone_number'])
    print "phone number normalized"
    if 'facebook_token' and 'facebook_id' in user_data:
        profile = Profile.objects.create(user=user, phone_number=user_data['phone_number'], normalized_phone=normalizedPhone, fb_token=user_data['facebook_token'], facebook_id=user_data['facebook_id'])
        update_facebook_friendships(user)
    else:
        profile = Profile.objects.create(user=user, phone_number=user_data['phone_number'], normalized_phone=normalizedPhone)
    print "Profile created"
    send_activation_code(profile)
    send_push_that_friend_joined.delay(profile)

    #if the person registering was a contact before, need to update invites to point to user instead
    contacts = get_contact_with_phone(user_data['phone_number'])
    print "Got contacts"
    # check_if_user_was_invited(contacts)
    for contact in contacts:
        bf_invites = BeaconFollow.objects.filter(contact=contact)
        for i in bf_invites:
            i.contact = None
            i.user = user
            i.save()

        ds_invites = DealStatus.objects.filter(contact=contact)
        for d in ds_invites:
            d.contact = None
            d.user = user
            d.save()
    check_if_user_was_referred(user)
    create_promo_code(user)
    send_welcome_email(user)
    if 'promo_code' in user_data:
        print "Checking Promo Code"
        check_promo_code(user, user_data['promo_code'])
    print "For loop completed"
    return user


def create_promo_code(user):
    promo_code = create_promo_string(user)
    new_promo_code = Promo(referring_user=user, item_number=1, promo_code=promo_code)
    new_promo_code.save()


def create_promo_string(user):
    four_digit_string = randint(1000, 9999)
    if user.last_name == "":
        promo_code = user.first_name + str(four_digit_string)
    else:
        promo_code = user.first_name + user.last_name[0:1] + str(four_digit_string)
    return promo_code.lower()


def update_user(user, user_data):
    if Profile.objects.filter(user=user).exists():
        user.set_password(user_data['password'])
        user.first_name = user_data['first_name']
        user.last_name = user_data['last_name']
        try:
            user.save()
            return True
        except Exception:
            return False
    else:
        return False


def add_device_and_assign_to_user(user, user_data):
    device = user_data['device_token']
    status_code = add_device(device)
    if status_code == 201:
        message = add_user_to_device(user, device)
        return message
    elif status_code == 200:
        add_user_to_device(user, device)
        return "Device already exists"
    else:
        return "Device not Saved"


def add_or_update_facebook_access_token(user, request_data):
    if 'fb_token' not in request_data:
        return False
    user.profile.fb_token = request_data['fb_token']
    user.profile.is_underage = check_if_user_is_underage(user.profile.fb_token)
    user.profile.save()
    update_facebook_id_and_name(user)
    update_facebook_friendships(user)
    return "Facebook token updated successfully"


def check_if_user_was_invited(contacts):
    time_cutoff = datetime.now()-timedelta(hours=12)
    if BeaconFollow.objects.filter(contact__in=contacts, state="G", date_created__gt=time_cutoff).exists():
        track_coupon_sms_sent(contacts[0].normalized_phone)
        get_free_drink_message = "Thanks for joining Hotspot! Here's your free drink coupon\n\nRedeem: http://bit.ly/1yi8sNT"
        send_sms(get_free_drink_message, [contacts[0].normalized_phone])


def check_if_user_is_underage(fb_token):
    try:
        graph_api = facebook.GraphAPI(access_token=fb_token)
        facebook_id = "theballroomseattle"
        events = graph_api.get_object(id=facebook_id + "/events")
        me = graph_api.get_object(id='me')
        statuses = graph_api.get_object(id=facebook_id + "/posts")
        return False
    except Exception:
        return True
