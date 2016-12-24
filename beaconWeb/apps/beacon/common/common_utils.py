import json
from django.utils.encoding import smart_str
from beaconWeb.common_utils import smart_format, safe_bulk_create, normalize_phone_number
from datetime import datetime, timedelta
from random import randint
from django.db.models import Q
from beaconWeb.apps.beacon.models.profile import Profile
from beaconWeb.common_utils import distance_between_two_points
from beaconWeb.apps.beacon.common.utils.encryption import simple_int_hash
from beaconWeb.apps.beacon.models.dating_profile import DatingProfile
from beaconWeb.apps.beacon.models.message import Message
from beaconWeb.apps.beacon.models.beacon_follow import BeaconFollow
from beaconWeb.apps.beacon.models.deal_status import DealStatus
from beaconWeb.apps.beacon.models.event_status import EventStatus
from beaconWeb.apps.beacon.models.cash_payment import CashPayment
from beaconWeb.apps.beacon.models.web_promo import WebPromo
from beaconWeb.apps.beacon.models.email_status import EmailStatus
from beaconWeb.apps.beacon.models.market import Market
from django.contrib.auth.models import User
from beaconWeb.apps.beacon.models.image import Image
from beaconWeb.apps.beacon.models.location import Location
from beaconWeb.apps.beacon.models.deal_place import DealPlace
from beaconWeb.apps.beacon.models.emails import Emails
from beaconWeb.apps.beacon.models.favorites import Favorites
from beaconWeb.apps.beacon.models.syndicated_events import SyndicatedEvents
from beaconWeb.apps.beacon.models.contact_status import ContactStatus
from beaconWeb.apps.beacon.models.unsubscribes import Unsubscribe
from beaconWeb.apps.beacon.models.contact import Contact
from beaconWeb.apps.beacon.models.sponsored_event import SponsoredEvent
from beaconWeb.apps.beacon.common.constants.message_type import MESSAGE_TYPE
from beaconWeb.apps.beacon.common.constants.beacon_status_values import BEACON_FOLLOW_STATUS
from beaconWeb.apps.beacon.common.constants.chat_type import CHAT_TYPE
from beaconWeb.apps.beacon.common.constants.event_status import EVENT_STATUS
# from beaconWeb.apps.beacon.retention.emails import send_error_email
import random
import string
from math import radians, cos, sin, asin, sqrt
from twilio.rest import TwilioRestClient
from django.conf import settings
from beaconWeb.apps.beacon.tasks.send_sms import send_sms, send_hotspot_message
from beaconWeb.apps.beacon.tasks.send_sms import send_individualized_sms
from django.db.models import Count
from boto.s3.connection import S3Connection
from beaconWeb.geo_timezone import GeoTimeZone
from ios_notifications.models import Device
from boto.s3.key import Key
from beaconWeb.apps.beacon.classes.guest import Guest
from beaconWeb.date_formatter import DateFormatter
import requests
from raven.contrib.django.models import client
from django.db import DatabaseError
from beaconWeb.apps.beacon.common.utils.events import adjust_to_server_timezone
import time
import facebook
import traceback
import braintree
from beaconWeb.apps.beacon.common.constants.event_type import EVENT_TYPE


#Helper functions
def get_first_time_contacts(contact_list):

    alreadyInvited = BeaconFollow.objects.filter(contact__in=contact_list).values_list('contact_id')
    alreadyInvitedContacts = list(Contact.objects.filter(pk__in=alreadyInvited))
    subtractedLists = [x for x in contact_list if x not in alreadyInvitedContacts]
    firstTimeContacts = list(remove_duplicate_contacts(subtractedLists))
    return firstTimeContacts


#Send message functions
def send_sms_invites(user, beacon, user_list, contact_list):
    # get your number so you dont get texts about your own hotspot
    if Profile.objects.filter(user=user).exists():
        profile = Profile.objects.get(user=user)
        normalized_phone = profile.normalized_phone

    first_time_body = smart_format("{0} {1} uses the app Hotspot (GetHotspotApp.com) to simplify meeting up with friends.", user.first_name, user.last_name)

    if user.last_name:
        notification_text = smart_format("{0} {1}: {2}", user.first_name, user.last_name, beacon.description)
    else:
        notification_text = smart_format("{0}: {1}", user.first_name, beacon.description)

    #add time and location info
    try:
        time_string = DateFormatter().friendly_string_for_timestamp(beacon.beacon_time, beacon.latitude, beacon.longitude)
        address_string = beacon.address
        notification_text += smart_format("\n{0} @ {1}", time_string, address_string)
    except:
        client.captureException()

    first_time_contacts = get_first_time_contacts(contact_list)


    # Add profiles and contacts to Beacon Follow (formerly Beacon Invites)
    beacon_invites = []
    profiles = Profile.objects.filter(user__in=user_list).exclude(normalized_phone=normalized_phone).select_related('user')

    for profile in profiles:
        beacon_invites.append(BeaconFollow(beacon=beacon, user=profile.user, invited_by=user,
                                           state=BEACON_FOLLOW_STATUS.INVITED))
    for contact in contact_list:
        beacon_invites.append(BeaconFollow(beacon=beacon, contact=contact, invited_by=user,
                                           state=BEACON_FOLLOW_STATUS.INVITED))

    BeaconFollow.objects.bulk_create(beacon_invites)

    beacon_invitations = BeaconFollow.objects.filter(beacon=beacon, contact__in=contact_list, invited_by=user,
                                                     state=BEACON_FOLLOW_STATUS.INVITED).select_related('user')

    # Create individualized messages for each Hotspot SMS
    contacts_sms_list = []
    sms_response_text = smart_format('Reply with "Yes" to let {0} know you can come or with "More" if you want more info',
                                     user.first_name)
    sms_message = smart_format("{0}\n\n{1}", notification_text, sms_response_text)
    for contact in contact_list:
        current_dict = {'contact_phone': contact.normalized_phone, 'message': sms_message}
        contacts_sms_list.append(current_dict)

    sms_users = User.objects.filter(pk__in=[o.pk for o in user_list],
                                    android_devices=None, ios_devices=None).select_related('profile')
    sms_profiles = [o.profile for o in sms_users]
    profile_sms_list = []
    for profile in sms_profiles:
        message = notification_text + "\nEvent details: Hotspot://Go-to-App"
        current_dict = {'profile_phone': profile.normalized_phone, 'message': message}
        profile_sms_list.append(current_dict)

    send_hotspot_message.delay(contacts=first_time_contacts, sms_text=first_time_body,
                               message_type=MESSAGE_TYPE.HOTSPOT_UPDATE, beacon_id=beacon.id)
    send_hotspot_message.delay(users=user_list, push_text=notification_text,
                               message_type=MESSAGE_TYPE.HOTSPOT_UPDATE, beacon_id=beacon.id)
    send_individualized_sms.delay(contacts_sms_list, profile_sms_list)
    return True


def create_hotspot_message_in_chat(beacon, chat_message, user, contact, avatar_url=None):
    Message.objects.create(user=user, contact=contact, beacon=beacon,
                           message=chat_message, chat_type=CHAT_TYPE.HOTSPOT_MESSAGE, avatar_url=avatar_url)


def send_hotspot_push_to_correct_profiles(beacon, push_message, message_type=None):
    users = users_to_notify(beacon, message_type=message_type)
    send_hotspot_message(users=users, push_text=push_message, message_type=MESSAGE_TYPE.MESSAGE, beacon_id=beacon.id)



def send_synchronous_sms(text_body, to):
    try:
        print "entered send sync sms function"
        twilio_client = TwilioRestClient(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        print "before sms message created"
        message = twilio_client.sms.messages.create(body=text_body, to=to, from_=settings.TWILIO_PHONE)
        print "Activation code sent"
        print message.sid
    except Exception as ex:
        if to != settings.TEST_ACCOUNT_NUMBER:
            raise ex


def send_activation_code(profile):
    code = generate_activation_code(profile)
    profile.activation_code = code
    profile.save()
    print "activation code generated and saved"
    text_body = "Hotspot Activation Code: {0}".format(code)
    if profile.normalized_phone != settings.TEST_ACCOUNT_NUMBER:
        send_synchronous_sms(text_body, "+1" + profile.normalized_phone)


def get_hotspot_guests(beacon):
    beacon_follows = BeaconFollow.objects.filter(beacon=beacon).select_related('user.profile', 'contact')
    guest_list = [Guest(follow) for follow in beacon_follows]

    return guest_list


#Add extra property functions
def add_extra_hotspot_properties(beacon):
    if Profile.objects.filter(user=beacon.creator).exists():
        beacon.profile = Profile.objects.get(user=beacon.creator)
    beacon.guests = get_hotspot_guests(beacon)

    if Image.objects.filter(user=beacon.creator, beacon=beacon).exists():
        image = Image.objects.filter(user=beacon.creator, beacon=beacon).latest('date_created')
        beacon.image_url = "https://s3.amazonaws.com/hotspot-photo/" + str(image.image_key)
    else:
        beacon.image_url = None

    if beacon.deal_statuses.exists():
        beacon.deal = beacon.deal_statuses.all()[0].deal
        beacon.deal.is_reward_item = False
        beacon.deal.is_followed = False
    else:
        beacon.deal = None



    #add six hours to beacon start time
    beacon.expiration = beacon.beacon_time + 21600
    images = list(Image.objects.filter(beacon=beacon))
    beacon.images = add_extra_image_properties(images)
    return beacon


def add_extra_image_properties(images):
    imagesWithExtraProperties = []
    for image in images:
        image.image_url = generate_image_url(image)
        imagesWithExtraProperties.append(image)
    return imagesWithExtraProperties


def is_hotspot_expired(beacon):
    return beacon.time + timedelta(hours=6) < datetime.now()


def get_user_hotspot(user):
    if BeaconFollow.objects.filter(user=user).latest('date_updated'):
            beacon_follow = BeaconFollow.objects.filter(user=user).latest('date_updated')
            if beacon_follow.beacon and not is_hotspot_expired(beacon_follow.beacon):
                beacon = beacon_follow.beacon
                return beacon
            else:
                return False
    else:
        return False


# Return users and contacts from list with elements like '{name: name, phone:phone}'
# Note: Contacts are created if they do not exist already.
def parse_json_into_users_and_contact_lists(user, list):
    new_list = []
    for c_json in list:
        c = json.loads(json.dumps(c_json))
        new_list.append(c)

    user_list = []
    contact_list = []
    for c in new_list:
        cobj = json.loads(c)
        if Profile.objects.filter(normalized_phone=normalize_phone_number(cobj['phone'])).exists():
            p = Profile.objects.get(normalized_phone=normalize_phone_number(cobj['phone']))
            user_list.append(p.user)
        else:
            if not Contact.objects.filter(user=user, name=cobj['name'], phone_number=cobj['phone'],
                                              normalized_phone=normalize_phone_number(cobj['phone'])).exists():
                contact = Contact(user=user, name=cobj['name'], phone_number=cobj['phone'],
                                      normalized_phone=normalize_phone_number(cobj['phone']))
                try:
                    contact.save()
                except DatabaseError:
                    client.captureException()
            else:
                contact = Contact.objects.filter(user=user, name=cobj['name'], phone_number=cobj['phone'],
                                                  normalized_phone=normalize_phone_number(cobj['phone'])).latest('date_created')
            contact_list.append(contact)

    return user_list, contact_list


def generate_activation_code(profile):
    if profile.normalized_phone == settings.TEST_ACCOUNT_NUMBER:
        return settings.TEST_ACCOUNT_ACTIVATION
    return generate_random_integer_string(4)


def generate_random_integer_string(stringLength):
    range_start = 10**(stringLength-1)
    range_end = (10**stringLength)-1
    return randint(range_start, range_end)


def fetch_bitly_url(url):
    request_url = "https://api-ssl.bitly.com/v3/shorten?access_token={0}&longUrl={1}".format(settings.BITLY_ACCESS_TOKEN, url)
    r = requests.get(request_url)
    r = r.json()
    if r['status_code'] == 200:
        return r['data']['url']
    else:
        return ""


def get_normalized_phonebook(user):
    profile = Profile.objects.get(user=user)
    if profile:
        myPhone = profile.normalized_phone

    normalized_phone_list = list(Contact.objects.filter(user=user).exclude(normalized_phone=myPhone).values_list('normalized_phone', flat=True))
    return normalized_phone_list


def remove_duplicate_contacts(contacts):
    new_contact_list = []
    contact_numbers = []
    for contact in contacts:
        if contact.normalized_phone not in contact_numbers:
            new_contact_list.append(contact)
            contact_numbers.append(contact.normalized_phone)
    return new_contact_list


def generate_image_url(image):
    s3Connection = S3Connection(settings.AWS_ACCESS_KEY_ID, settings.AWS_SECRET_ACCESS_KEY)
    bucket = s3Connection.get_bucket('hotspot-photo')
    imageKey = Key(bucket)
    imageKey.key = image.image_key
    url = "http://s3.amazonaws.com/hotspot-photo/" + imageKey.key
    # url = imageKey.generate_url(expires_in=10000)
    return url


def users_to_notify(beacon, user=None, message_type=None):
    creator = beacon.creator
    if message_type and message_type == MESSAGE_TYPE.HOTSPOT_JOIN:
        return [beacon.creator]

    attendees = []
    attending_objects = BeaconFollow.objects.\
        filter(Q(state=BEACON_FOLLOW_STATUS.GOING) | Q(state=BEACON_FOLLOW_STATUS.HERE)).filter(beacon=beacon).select_related('user')
    for bf_objects in attending_objects:
        if bf_objects.user:
            attendees.append(bf_objects.user)
    message_senders = []
    message_objects = Message.objects.filter(beacon=beacon, chat_type=CHAT_TYPE.USER_MESSAGE).select_related('user')
    for message in message_objects:
        if message.user is not None:
            message_senders.append(message.user)
    users = set(attendees + message_senders + [creator])
    if user:
        if user in users:
            users.remove(user)
    return users


def text_app_link(phone):
    textBody = "Download Hotspot here and get your first drink (up to $5) for free:\nhttp://GetHotspotApp.com"
    if not Profile.objects.filter(normalized_phone=phone).exists():
        contact_status = ContactStatus(phone_number=phone)
        contact_status.save()
    send_sms(textBody, [phone])

def text_app_link_no_free_drink(phone):
    textBody = "Download Hotspot here:\nhttp://GetHotspotApp.com"
    send_sms(textBody, [phone])


def add_venmo_token_for_user(user_id, access_token):
    user = User.objects.get(pk=int(user_id))
    user.profile.venmo_auth_token = access_token
    user.profile.is_venmo_enabled = True
    user.profile.save()


def get_users_within_distance(lat, lng, distance=10, max_date=datetime.now(), min_date=datetime.now()-timedelta(weeks=52)):
    lat_range = [lat-1, lat+1]
    lng_range = [lng-1, lng+1]
    locations = Location.objects.filter(latitude__range=lat_range, longitude__range=lng_range, date_created__range=[min_date, max_date])
    users_in_location = []
    for location in locations:
        dist = distance_between_two_points(lat, lng, location.latitude, location.longitude)
        if dist < distance:
            if location.user_id not in users_in_location:
                users_in_location.append(location.user_id)
    user_obj = User.objects.filter(pk__in=users_in_location)
    return user_obj


def get_deal_places_within_distance(user, lat, lng, radius=1):
    venues_within_distance = []
    lat_range = [lat - 0.1, lat + 0.1]
    lng_range = [lng - 0.1, lng + 0.1]
    user_favorites = Favorites.objects.filter(user=user, active=True).values_list('place', flat=True)
    venues = DealPlace.objects.filter(latitude__range=lat_range, longitude__range=lng_range).exclude(pk__in=user_favorites)
    for venue in venues:
        distance = distance_between_two_points(lat, lng, venue.latitude, venue.longitude)
        if distance < radius:
            venues_within_distance.append(venue)
    return venues_within_distance


def get_venue_recommendations(user):
    if Location.objects.filter(user=user).exists():
        last_user_location = Location.objects.filter(user=user).latest('date_created')
        latitude = last_user_location.latitude
        longitude = last_user_location.longitude
    else:
        latitude = 47.6278645
        longitude = -122.3158121
    venues = get_deal_places_within_distance(user, latitude, longitude)
    updated_venues = []
    if len(venues) > 3:
        for venue in venues:
            new_venue = {}
            new_venue['number_of_followers'] = len(Favorites.objects.filter(place=venue))
            new_venue['name'] = venue.name
            new_venue['image_url'] = venue.image_url
            new_venue['description'] = venue.place_description
            new_venue['deal_place_id'] = venue.id
            updated_venues.append(new_venue)
        updated_venues.sort(key=lambda x: x['number_of_followers'], reverse=True)
    else:
        for i in range(3):
            new_venue = {}
            new_venue['number_of_followers'] = ""
            new_venue['name'] = ""
            new_venue['image_url'] = ""
            new_venue['description'] = ""
            new_venue['deal_place_id'] = ""
            updated_venues.append(new_venue)
    return updated_venues


def unsubscribe_emails(emails):
    for email in emails:
        unsubscribe = Unsubscribe(email=email)
        unsubscribe.save()


def add_facebook_event_as_sponsored_event(event_id):
    user = User.objects.get(username="5413359388")
    facebook_api = facebook.GraphAPI(access_token=user.profile.fb_token)
    try:
        event = facebook_api.get_object(id=event_id)
        add_sponsored_event_to_syndicated_events(event)
    except Exception:
        print "FEED FAILED FACEBOOK"
        traceback.print_exc()


def add_sponsored_event_to_syndicated_events(event):
    facebook_id = event['venue']['id']
    place = DealPlace.objects.get(facebook_id=facebook_id)
    title = event['name'].encode('ascii', 'ignore')
    date = event['start_time']
    truncated_date = date.split(':')[0] + ":" + date.split(':')[1]
    stripped_date = datetime.strptime(truncated_date,"%Y-%m-%dT%H:%M")
    event_id = str(event['id'])
    if not SyndicatedEvents.objects.filter(event_id=event_id).exists():
        add_sponsored_event(place, title, adjust_to_server_timezone(stripped_date), event_id)


def add_sponsored_event(place, title, date, event_id):
    link = "https://www.facebook.com/events/" + str(event_id)
    syndicated_event = SyndicatedEvents(place=place, title=title, event_id=event_id, event_type=EVENT_TYPE.SPONSORED,  website=link, start=date)
    syndicated_event.save()


def get_users_from_prior_events():
    deal_ids = [178, 207, 210, 213]
    user_ids = DealStatus.objects.filter(deal_id__in=deal_ids, deal_status="R").values_list('user', flat=True)
    users = User.objects.filter(pk__in=user_ids)
    return users


def process_refund(event_status):
    if event_status.payment.payment_authorization:
        transaction_id = event_status.payment.payment_authorization
        result = braintree.Transaction.refund(str(transaction_id))
        if result.is_success:
            event_status.refund_authorization = result.transaction.id
            event_status.save()
            print "Refund Successful"
        else:
            print str(result.errors.deep_errors)
    else:
        print "No Payment Auth"


def is_presale(sponsored_event):
    if sponsored_event.presale_cap:
        attendee_count = EventStatus.objects.filter(event=sponsored_event, refund_authorization__isnull=True).filter(Q(status="U") | Q(status="R")).count()
        if sponsored_event.presale_cap > attendee_count:
            return True
        else:
            return False
    else:
        presale_cutoff = sponsored_event.start - timedelta(hours=18)
        if datetime.now() > presale_cutoff:
            return False
        else:
            return True


def add_presale_property(sponsored_event):
    sponsored_event.presale_active = is_presale(sponsored_event)
    return sponsored_event


def get_presale_status(event_status):
    sponsored_event = event_status.event
    return is_presale(sponsored_event)


def get_presale_status_from_event(event):
    return is_presale(event)


def get_all_attendee_list(event):
    event_statuses = EventStatus.objects.filter(event=event).filter(Q(status="U")|Q(status="R"))
    return list(event_statuses)


def get_attendee_counts(event):
    unredeemed = EventStatus.objects.filter(event=event, status="U")
    redeemed = EventStatus.objects.filter(event=event, status="R")
    web_reservation_count = get_web_reservation_count(event)
    return str(len(unredeemed)), str(len(redeemed)), web_reservation_count, str(len(unredeemed) + len(redeemed) + web_reservation_count)


def get_web_reservation_count(event):
    web_reservations = CashPayment.objects.filter(event=event, name__isnull=False)
    count = 0
    for reservation in web_reservations:
        count = count + reservation.attendees
    return count


def update_market_timezones():
    markets = Market.objects.all()
    for market in markets:
        timezone_id = GeoTimeZone().get_timezone_id(latitude=market.latitude, longitude=market.longitude)
        market.timezone_id = timezone_id
        market.save()


def get_timezone_for_event(event):
    return event.market.timezone_id
    # lat = event.place.latitude
    # lng = event.place.longitude
    # lat_range = [lat-1, lat+1]
    # lng_range = [lng-1, lng+1]
    # markets = Market.objects.filter(latitude__range=lat_range, longitude__range=lng_range)
    # market = get_nearest_market(lat, lng, markets)
    # if market:
    #     print "Market Found"
    #     return GeoTimeZone().get_python_timezone(market.timezone_id)
    # else:
    #     print "Market Not Found"
    #     return GeoTimeZone().get_timezone(latitude=lat, longitude=lng)


def get_nearest_market(lat, lng, markets):
    current_distance = 100000
    closest_market = None
    for market in markets:
        dist = distance_between_two_points(lat, lng, market.latitude, market.longitude)
        if dist < current_distance:
            current_distance = dist
            closest_market = market
    return closest_market


def get_market_from_lat_lng(lat, lng):
    lat_range = [lat - 1, lat + 1]
    lng_range = [lng - 1, lng + 1]
    markets = Market.objects.filter(latitude__range=lat_range, longitude__range=lng_range)
    market = get_nearest_market(lat, lng, markets)
    return market


def get_market_for_event(event):
    lat = event.place.latitude
    lng = event.place.longitude
    market = get_market_from_lat_lng(lat, lng)
    return market


def update_markets_for_events():
    all_events = SponsoredEvent.objects.all()
    for event in all_events:
        market = get_market_for_event(event)
        event.market = market
        event.save()


def text_payment_link(request_data):
    if not 'phone_number' and 'event_id' in request_data:
        return False
    phone_number = normalize_phone_number(request_data['phone_number'])
    event_id = int(request_data['event_id'])
    if SponsoredEvent.objects.filter(pk=event_id).exists():
        event = SponsoredEvent.objects.get(pk=event_id)
        payment_url = get_shortened_payment_url(event)
        text_body = "Payment link for the Hotspot event at {0}:\n\n{1}".format(event.place.name, payment_url)
        send_sms(text_body, [phone_number])
    else:
        return False


def get_shortened_payment_url(event):
    shortened_url = "{0}/payment/{1}".format(settings.URL, event.id)
    shortened_url = fetch_bitly_url(shortened_url)
    # shortened_url = shortened_url.strip('http://')
    return shortened_url


def get_current_web_price(event):
    if datetime.now() > event.end - timedelta(hours=1):
        return float(event.web_item_price / 2)
    else:
        return event.web_item_price


def get_current_app_price(event):
    if get_presale_status_from_event(event):
        return event.presale_item_price
    else:
        return event.item_price


def check_into_event(request_data):
    status_id = int(request_data['status_id'])
    is_app_reservation = json.loads(request_data['app_reservation'])
    if is_app_reservation:
        event_status = EventStatus.objects.get(pk=status_id)
        event_status.status = EVENT_STATUS.REDEEMED
        event_status.save()
    else:
        cash_payment = CashPayment.objects.get(pk=status_id)
        cash_payment.status = EVENT_STATUS.REDEEMED
        cash_payment.save()
    print "IS APP RESERVATION: " + str(is_app_reservation)
    print str(status_id)


def add_email(email, market):
    email = Emails(email=email, market=market)
    email.save()


def add_email_with_event(email, market, event):
    email = Emails(email=email, market=market, event=event)
    email.save()

def id_generator(size=6, chars=string.ascii_uppercase + string.digits):
   return ''.join(random.choice(chars) for _ in range(size))


def create_web_promo_code_presale(event):
    new_code = id_generator()
    price = '{:,.2f}'.format(event.presale_item_price)
    content = '''With this promo code, you can purchase multiple tickets through the website for ${0}!'''.format(price)
    web_promo = WebPromo(code=new_code, event=event, price=event.presale_item_price, content=content)
    web_promo.save()
    return new_code


def create_web_promo_code_same_day(event):
    new_code = id_generator()
    price = '{:,.2f}'.format(event.item_price)
    content = '''With this promo code, you can purchase multiple tickets through the website for ${0}!'''.format(price)
    web_promo = WebPromo(code=new_code, event=event, price=event.item_price, content=content)
    web_promo.save()
    return new_code


def store_email_status(request_data):
    try:
        for request in request_data:
            category = request['category'][0]
            event = request['event']
            email = request['email']
            if 'useragent' in request:
                user_agent = request['useragent']
            else:
                user_agent = None
            if 'url' in request:
                url = request['url']
            else:
                url = None
            email_status = EmailStatus(email=email, category=category, event=event, user_agent=user_agent, url=url)
            email_status.save()
    except:
        # html = "Storing email status error"
        traceback.print_exc()
        # html = html + str(traceback.format_exc())
        # send_error_email(html)


def get_new_submitted_emails(min_date=datetime.now()-timedelta(weeks=1), max_date=datetime.now()):
    markets = Market.objects.all()
    emails = Emails.objects.filter(market__in=markets, date_created__gte=min_date, date_created__lte=max_date)
    return emails


def get_all_new_users_in_markets_emails(min_date=datetime.now()-timedelta(weeks=1), max_date=datetime.now()):
    markets = Market.objects.all()
    user_emails = []
    for market in markets:
        emails = get_new_users_within_distance_emails(market.latitude, market.longitude, max_date, min_date)
        user_emails.extend(emails)
    return set(user_emails)


def get_all_new_users_in_markets(min_date=datetime.now()-timedelta(weeks=1), max_date=datetime.now()):
    markets = Market.objects.all()
    users = []
    for market in markets:
        users_in_market = get_new_users_within_distance(market.latitude, market.longitude, max_date, min_date)
        users.extend(users_in_market)
    return set(users)



def get_new_users_within_distance_emails(lat, lng, max_date = datetime.now(), min_date = datetime(2014, 9, 1)):
    lat_range = [lat-0.3, lat+0.3]
    lng_range = [lng-0.3, lng+0.3]
    users_in_location = Location.objects.filter(latitude__range=lat_range, longitude__range=lng_range).values_list('user', flat=True)
    user_emails = User.objects.filter(pk__in=users_in_location, date_joined__gte=min_date, date_joined__lte=max_date).exclude(email="").values_list('email', flat=True)
    return list(user_emails)


def get_new_users_within_distance(lat, lng, max_date = datetime.now(), min_date = datetime(2014, 9, 1)):
    lat_range = [lat-0.3, lat+0.3]
    lng_range = [lng-0.3, lng+0.3]
    users_in_location = Location.objects.filter(latitude__range=lat_range, longitude__range=lng_range).values_list('user', flat=True)
    users = User.objects.filter(pk__in=users_in_location, date_joined__gte=min_date, date_joined__lte=max_date)
    return list(users)


def get_dating_profiles_for_event(event):
    user_ids = EventStatus.objects.filter(event=event).exclude(status="I").exclude(status="N").values_list('user', flat=True)
    users = User.objects.filter(pk__in=user_ids)
    profiles = []
    for user in users:
        profiles.append(user.profile)
    dating_profiles = DatingProfile.objects.filter(dating_profile__in=profiles)
    return dating_profiles


def get_next_event_in_market(market):
    upcoming_events = SponsoredEvent.objects.filter(start__gte=datetime.now(), active=True).order_by('start')
    for event in upcoming_events:
        new_market = get_market_for_event(event)
        if market == new_market:
            return event
    return None


def get_four_nearest_events(event):
    upcoming_events = SponsoredEvent.objects.filter(start__gte=datetime.now()).exclude(pk=event.id)
    # for event in upcoming_events:
    #     event.link_url = "{0}/tickets/{1}".format(settings.URL, simple_int_hash(event.id))
    # # furthest_away = 1000000
    # # closest_events = []
    # # for e in upcoming_events:
    # #     pass
    return upcoming_events.order_by("?")[:4]
