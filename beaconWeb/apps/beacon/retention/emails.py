import sendgrid
from beaconWeb.apps.beacon.models.unsubscribes import Unsubscribe
from beaconWeb.apps.beacon.models.emails import Emails
from django.conf import settings
from django.contrib.auth.models import User
from beaconWeb.apps.beacon.models import Contact
from beaconWeb.common_utils import distance_between_two_points
from beaconWeb.apps.beacon.models import Location
from beaconWeb.apps.beacon.models import EmailResponse
from beaconWeb.apps.beacon.models import SponsoredEvent
from beaconWeb.apps.beacon.models import EventStatus
from beaconWeb.apps.beacon.models import UserFeedback
from beaconWeb.apps.beacon.models import CashPayment
from beaconWeb.apps.beacon.models import DealStatus
from beaconWeb.apps.beacon.models import DealPlace
from beaconWeb.apps.beacon.models import Favorites
from beaconWeb.apps.beacon.models import Deal
from beaconWeb.apps.beacon.models import Market
from django.db.models import Q
# from beaconWeb.apps.beacon.common.common_utils import get_market_from_lat_lng
from beaconWeb.apps.beacon.analytics.updated_analytics import get_venues_within_distance, get_user_within_distance, get_notifications_by_venue, excluded_users, get_venues_within_distance_for_events
from beaconWeb.apps.beacon.common.utils.tracker import track_notification
from beaconWeb.apps.beacon.common.constants.notification_types import NOTIFICATION_TYPE
from beaconWeb.apps.beacon.common.constants.email_campaign_type import EMAIL_CAMPAIGN_TYPE
from beaconWeb.apps.beacon.retention.constants import *
from beaconWeb.apps.beacon.common.utils.events import get_events_for_user
from beaconWeb.apps.beacon.common.utils.encryption import simple_int_hash
from beaconWeb.apps.beacon.models.email_campaign_tracker import EmailCampaignTracker
from beaconWeb.geo_timezone import GeoTimeZone
from beaconWeb.apps.beacon.common.common_utils import get_current_app_price
from datetime import datetime, timedelta
from beaconWeb.apps.beacon.models import NotificationTracker
from beaconWeb.apps.beacon.common.constants.email_status import EMAIL_STATUS
import pytz


#Email Helper Functions
def send_message(message):
    s = sendgrid.Sendgrid(settings.EMAIL_HOST_USER, settings.EMAIL_HOST_PASSWORD, secure=True)
    try:
        s.smtp.send(message)
    except:
        print "Send message failed"


def create_marketing_email(from_address, to_address, subject, plaintext, html, category):
    message = sendgrid.Message(from_address, subject, plaintext, html)
    try:
        message.add_to(to_address)
    except message.DoesNotExist:
        print "To field does not exist"
    message.add_category(category)
    return message


def get_friend_numbers():
    jas = User.objects.get(username='5413359388')
    jeff = User.objects.get(username='6176337532')
    either = Q(user=jeff) | Q(user=jas)
    friend_numbers = Contact.objects.filter(either).values_list('normalized_phone', flat=True)
    return friend_numbers


def get_non_friend_emails():
    emails = []
    users = User.objects.filter(profile__activated=True)
    friend_numbers = get_friend_numbers()
    friends_excluded = users.exclude(profile__normalized_phone__in=friend_numbers)
    for user in friends_excluded:
        if user.email != "":
            emails.append(user.email)
    return emails


def get_friend_emails():
    emails = []
    users = User.objects.filter(profile__activated=True)
    friend_numbers = get_friend_numbers()
    friends_included = users.filter(profile__normalized_phone__in=friend_numbers)
    for user in friends_included:
        if user.email != "":
            emails.append(user.email)
    return emails


def get_email_recipients(first_recipient, last_recipient):
    users = User.objects.filter(pk__range=(first_recipient, last_recipient))
    emails = []
    deal_emails = []
    locations = Location.objects.filter(user__in=users)
    for location in locations:
        dist = distance_between_two_points(41.300093,-72.9262206, location.latitude, location.longitude)
        if dist < 5:
            if location.user.email not in deal_emails and location.user.email != "":
                deal_emails.append(location.user.email)
    for user in users:
        if user.email != "" and user.email not in deal_emails:
            emails.append(user.email)
    return emails, deal_emails


def generate_deals_welcome_message(lat, lng, distance):
    html = generate_deals_welcome_message_html
    deals = Deal.objects.filter(active=True)
    place_names = []
    for deal in deals:
        dist = distance_between_two_points(lat, lng, deal.place.latitude, deal.place.longitude)
        if dist < distance:
            place_names.append(deal.place.name)
    last_item = place_names.pop()
    deal_place_string = (", ".join(place_names) + " and " + last_item + ".").replace("'", "")
    new_html = html.replace("{0}", deal_place_string)
    return new_html


#Specific Email Functions
def send_marketing_email(from_address, from_title, recipients, subject, plaintext, html, category):
    original_unsubcribes = Unsubscribe.objects.all().values_list('email', flat=True)
    email_response_unsubscribes = EmailResponse.objects.filter(status=EMAIL_STATUS.UNSUBSCRIBE).values_list('email', flat=True)
    unsubscribes = list(original_unsubcribes) + list(email_response_unsubscribes)
    for recipient in recipients:
        if recipient.lower() not in unsubscribes:
            message = create_marketing_email((from_address, from_title), recipient, subject, plaintext, html, category)
            send_message(message)
            print recipient


def send_feedback_email(user, venue):
    info = "This user just had an issue at {0}".format(venue.name)
    send_marketing_email(user.email, user.first_name, ["info@gethotspotapp.com"], "Hotspot Deal Feedback", info, info, "deal_feedback")


def send_welcome_email(user):
    subject = "Welcome to Hotspot!"
    html = send_welcome_email_html
    plaintext = send_welcome_email_plaintext
    from_address = "rachael.olsen@gethotspotapp.com"
    message = create_marketing_email((from_address, "Hotspot"), [user.email], subject, plaintext, html, "welcome_email")
    send_message(message)


def get_new_deals():
    deal_places = get_venues_within_distance(47.6369484, -122.3625873, 20)
    new_deals = Deal.objects.filter(place__in=deal_places, recently_added=True)
    return list(new_deals)


def change_recently_added_to_false():
    new_deals = get_new_deals()
    for deal in new_deals:
        deal.recently_added = False
        deal.save()


# def send_new_deal_emails_to_users():
#     users = get_user_within_distance(47.6369484, -122.3625873, 20)
#     new_deals = get_new_deals()
#     sponsored_events = get_sponsored_events(None, 47.6369484, -122.3625873)
#     emails_sent = 0
#     for user in users:
#         message_detail = str(len(new_deals))
#         emails_sent += 1
#         events = get_events_for_user(user)
#         print message_detail
#         send_new_deal_email(user, new_deals, sponsored_events, events)
#         track_notification(user, NOTIFICATION_TYPE.NEW_HOTSPOTS_EMAIL, message_detail)
#     print "Emails sent: " + str(emails_sent)


def get_filtered_deals(user, min_date, max_date):
    deal_places = []
    user_locations = Location.objects.filter(user=user).order_by('-date_created')[:10]
    for location in user_locations:
        deal_places.extend(get_venues_within_distance(location.latitude, location.longitude, 20))
    new_deals = Deal.objects.filter(place__in=deal_places, date_created__gte=min_date, date_created__lte=max_date).distinct('place')
    # filtered_deals = []
    # for place in deal_places:
    #     if new_deals.filter(place=place).count() == 1:
    #         filtered_deals.append(new_deals.get(place=place))
    #     elif new_deals.filter(place=place).exclude(invite_requirement=1).count() >= 1:
    #         filtered_deals.append(new_deals.filter(place=place).exclude(invite_requirement=1)[0])
    return new_deals


def send_event_feedback_email(user, event):
    base_url = settings.URL + "/feedback/"
    user_id_hash = simple_int_hash(user.id)
    event_id_hash = simple_int_hash(event.id)
    html = user_event_feedback_email_html.replace("{{venue}}", event.place.name)
    plaintext = user_event_feedback_email_plaintext.replace("{{venue}}", event.place.name)
    subject_line = "How was the event at {0}?".format(event.place.name)
    for x in range(1, 11):
        old = "{{Url " + str(x) + "}}"
        new = base_url + str(user_id_hash) + "/" + str(event_id_hash) + "/" + str(x) + "/"
        html = html.replace(old, new)
        plaintext = plaintext.replace(old, new)
    send_marketing_email("jas@gethotspotapp.com", "Jasjit Singh", [user.email], subject_line, plaintext, html, "feedback_email")


def send_event_feedback_emails_to_users():
    last_event_feedback_email = NotificationTracker.objects.filter(notification_type="EF").latest('date_created')
    current_date = datetime.now()
    print "Last request sent {0}".format(str(last_event_feedback_email.date_created))
    events_in_range = SponsoredEvent.objects.filter(start__gt=last_event_feedback_email.date_created, start__lte=current_date, active=True)
    redeemed = EventStatus.objects.filter(event__in=events_in_range, status="R",refund_authorization__isnull=True)
    for event in events_in_range:
        r = redeemed.filter(event=event)
        print event.place.name + " " + event.start.strftime("%Y-%m-%d") + " " + str(len(r))
    terminal_answer = raw_input("Email these? y/n ").lower() == 'y'
    if terminal_answer is True:
        for status in redeemed:
            if status.user.email != "" and status.user.email is not None:
                send_event_feedback_email(status.user,status.event)
                track_notification(status.user, NOTIFICATION_TYPE.EVENT_FEEDBACK_EMAIL, status.event.place.name)


def send_event_feedback_interview_requests(no_email, after_date=datetime(2015, 1, 1)):
    last_interview_request = NotificationTracker.objects.filter(notification_type="IR").latest('date_created')
    print "Last request send {0}".format(str(last_interview_request))
    already_emailed_ids = NotificationTracker.objects.filter(notification_type="IR").values_list('recipient')
    already_emailed = User.objects.filter(pk__in=already_emailed_ids) | User.objects.filter(pk__in=no_email)
    responses = UserFeedback.objects.filter(date_created__gt=after_date).filter(date_created__gt=last_interview_request.date_created).distinct('user','sponsored_event').exclude(user__in=already_emailed)
    event_ids = responses.values_list('sponsored_event', flat=True)
    events = SponsoredEvent.objects.filter(pk__in=event_ids).filter(date_created__gte=after_date)
    for event in events:
        n_responses = responses.filter(sponsored_event=event)
        print "{0}: {1} respondents".format(event.place.name, str(len(n_responses)))
        for response in n_responses:
            print response.user.first_name + " " + response.user.last_name + " " + str(response.user.id) + " " + response.user.email + " " + str(response.nps_score)
        print ""
    terminal_answer = raw_input("Email these? y/n ").lower() == 'y'
    if terminal_answer is True:
        for response in responses:
            favorability = "."
            if response.nps_score < 6:
                favorability = ", though I'm sorry the event wasn't great for you."
            previous_IR_emails = NotificationTracker.objects.filter(notification_type="IR", recipient=response.user)
            print response.user.first_name + " " + str(response.nps_score)
            if len(previous_IR_emails) < 1:
                html = user_interview_request_events_html.replace("{{first_name}}",response.user.first_name,).replace("{{venue}}", response.sponsored_event.place.name).replace("{{favorability}}", favorability)
                plaintext = user_interview_request_events_plaintext.replace("{{first_name}}",response.user.first_name,).replace("{{venue}}", response.sponsored_event.place.name).replace("{{favorability}}", favorability)
                send_marketing_email("jas@gethotspotapp.com", "Jasjit Singh", [response.user.email], "Hotspot feedback", plaintext, html, "user_interview_request")
                track_notification(response.user, NOTIFICATION_TYPE.USER_INTERVIEW_REQUEST, response.sponsored_event.place.name)
            else:
                print "Already emailed {0}".format(str(response.user.id))


def get_date_string(date):
    date = date - timedelta(hours=2)
    if date > datetime.now() + timedelta(weeks=1):
        return date.strftime("%B %d, %I:%M%p").lstrip("0").replace(" 0", " ")
    else:
        return date.strftime("%A, %I:%M%p").lstrip("0").replace(" 0", " ")

# def get_date_string(date):
#     date = date + timedelta(hours=1)
#     if date > datetime.now() + timedelta(weeks=1):
#         return date.strftime("%B %d, %I:%M%p").lstrip("0").replace(" 0", " ")
#     else:
#         return date.strftime("%A, %I:%M%p").lstrip("0").replace(" 0", " ")


# def get_date_string(date):
#     date = date - timedelta(hours=1)
#     if date > datetime.now() + timedelta(weeks=1):
#         return date.strftime("%B %d, %I:%M%p").lstrip("0").replace(" 0", " ")
#     else:
#         return date.strftime("%A, %I:%M%p").lstrip("0").replace(" 0", " ")


def get_date_string_for_sponsored_event(date):
    date = date - timedelta(hours=2)
    if date > datetime.now() + timedelta(weeks=1):
        return date.strftime("%B").lstrip("0").replace(" 0", " ")
    else:
        return date.strftime("%A").lstrip("0").replace(" 0", " ")


def send_weekly_event_promotion_email(event, subject):
    event_place_latitude = event.place.latitude
    event_place_longitude = event.place.longitude
    users = get_user_within_distance(event_place_latitude, event_place_longitude, 40)
    for user in users:
        send_event_marketing_email(user, event, subject)
    print str(len(users)) + " emails sent for " + str(event.place.name)


def send_presale_email(sponsored_event, subject):
    users = get_user_within_distance(sponsored_event.place.latitude, sponsored_event.place.longitude, 20)
    for user in users:
        send_sponsored_event_email(user, sponsored_event, subject)


def send_sponsored_event_email(user, sponsored_event, subject):
    top_of_email = weekly_email_top_of_email.replace("{{user_full_name}}", user.get_full_name()).replace("{{date_sent}}", datetime.now().strftime("%B %d, %Y").lstrip("0").replace(" 0", " "))
    regular_event_section = weekly_email_event_section_template
    # sponsored_event_section = weekly_email_sponsored_event_section_template
    deal_section = weekly_email_deal_section_template
    bottom_of_email = weekly_email_bottom_of_email.replace("{{promo_code}}", user.profile.promo_code)
    full_email = top_of_email
    # if len(sponsored_events) > 0:
    full_email = full_email + sponsored_event_section_header
    # for index, event in enumerate(sponsored_events):
    date_string = get_date_string(sponsored_event.start)
    new_event_section = regular_event_section.replace("{{venue_image}}", sponsored_event.place.image_url).replace("{{venue_name}}", sponsored_event.place.name).replace("{{event_name}}", sponsored_event.title).replace("{{event_link}}", sponsored_event.web_url).replace("{{day_and_time}}", date_string)
    full_email = full_email + new_event_section
    events = get_events_for_user(user)
    if len(events) > 0:
        full_email = full_email + event_section_header
        for index, event in enumerate(events):
            date_string = get_date_string(event.start)
            new_event_section = regular_event_section.replace("{{venue_image}}", event.place.image_url).replace("{{venue_name}}", event.place.name).replace("{{event_name}}", event.title).replace("{{event_link}}", event.website).replace("{{day_and_time}}", date_string)
            full_email = full_email + new_event_section
    full_email = full_email + bottom_of_email
    plaintext = send_new_deal_email_plaintext
    plaintext = plaintext.replace("{{Promo Code}}", user.profile.promo_code)
    if user.email != "" and user.email is not None:
        send_marketing_email("info@gethotspotapp.com", "Hotspot", [user.email], subject, plaintext, full_email, subject)


def send_sponsored_events_email(user, sponsored_events, subject):
    top_of_email = weekly_email_top_of_email.replace("{{user_full_name}}", user.get_full_name()).replace("{{date_sent}}", datetime.now().strftime("%B %d, %Y").lstrip("0").replace(" 0", " "))
    regular_event_section = weekly_email_event_section_template
    # sponsored_event_section = weekly_email_sponsored_event_section_template
    deal_section = weekly_email_deal_section_template
    bottom_of_email = weekly_email_bottom_of_email.replace("{{promo_code}}", user.profile.promo_code)
    full_email = top_of_email
    # if len(sponsored_events) > 0:
    full_email = full_email + sponsored_event_section_header
    # for index, event in enumerate(sponsored_events):
    for sponsored_event in sponsored_events:
        date_string = get_date_string(sponsored_event.start)
        new_event_section = regular_event_section.replace("{{venue_image}}", sponsored_event.place.image_url).replace("{{venue_name}}", sponsored_event.place.name).replace("{{event_name}}", sponsored_event.title).replace("{{event_link}}", sponsored_event.web_url).replace("{{day_and_time}}", date_string)
        full_email = full_email + new_event_section
    events = get_events_for_user(user)
    if len(events) > 0:
        full_email = full_email + event_section_header
        for index, event in enumerate(events):
            date_string = get_date_string(event.start)
            new_event_section = regular_event_section.replace("{{venue_image}}", event.place.image_url).replace("{{venue_name}}", event.place.name).replace("{{event_name}}", event.title).replace("{{event_link}}", event.website).replace("{{day_and_time}}", date_string)
            full_email = full_email + new_event_section
    full_email = full_email + bottom_of_email
    plaintext = send_new_deal_email_plaintext
    plaintext = plaintext.replace("{{Promo Code}}", user.profile.promo_code)
    if user.email != "" and user.email is not None:
        send_marketing_email("info@gethotspotapp.com", "Hotspot", [user.email], subject, plaintext, full_email, subject)


def send_new_deal_email(user, new_deals, sponsored_events, events):
    top_of_email = weekly_email_top_of_email.replace("{{user_full_name}}", user.get_full_name()).replace("{{date_sent}}", datetime.now().strftime("%B %d, %Y").lstrip("0").replace(" 0", " "))
    regular_event_section = weekly_email_event_section_template
    # sponsored_event_section = weekly_email_sponsored_event_section_template
    deal_section = weekly_email_deal_section_template
    bottom_of_email = weekly_email_bottom_of_email.replace("{{promo_code}}", user.profile.promo_code)
    full_email = top_of_email

    if len(sponsored_events) > 0:
        full_email = full_email + sponsored_event_section_header
        for index, event in enumerate(sponsored_events):
            date_string = get_date_string(event.start)
            new_event_section = regular_event_section.replace("{{venue_image}}", event.place.image_url).replace("{{venue_name}}", event.place.name).replace("{{event_name}}", event.title).replace("{{event_link}}", event.web_url).replace("{{day_and_time}}", date_string)
            full_email = full_email + new_event_section

    if len(events) > 0:
        full_email = full_email + event_section_header
        for index, event in enumerate(events):
            date_string = get_date_string(event.start)
            new_event_section = regular_event_section.replace("{{venue_image}}", event.place.image_url).replace("{{venue_name}}", event.place.name).replace("{{event_name}}", event.title).replace("{{event_link}}", event.website).replace("{{day_and_time}}", date_string)
            full_email = full_email + new_event_section

    if len(new_deals) > 0:
        full_email = full_email + deal_section_header
        for index, deal in enumerate(new_deals):
            new_deal_section = deal_section.replace("{{venue_image}}", deal.place.image_url).replace("{{original_price}}", "$" + str(int(deal.item_market_price))).replace("{{new_price}}", "$" + str(int(deal.item_price))).replace("{{item_name}}", deal.item_name).replace("{{venue_name}}", deal.place.name).replace("{{venue_description}}", deal.place.place_description)
            full_email = full_email + new_deal_section
    full_email = full_email + bottom_of_email
    plaintext = send_new_deal_email_plaintext
    plaintext = plaintext.replace("{{Promo Code}}", user.profile.promo_code)
    if user.email != "" and user.email is not None:
        send_marketing_email("info@gethotspotapp.com", "Hotspot", [user.email], "Weekly Report", plaintext, full_email, "weekly_report")


def format_date(date):
      return date.strftime('%m/%d/%Y')


def send_receipt(redeemed, last_successful_settlement, current_date, total_cost):
    top_html = send_receipt_top_html
    middle_html = send_receipt_middle_html
    combined_middle_html = ""
    for deal_status in redeemed:
        new_middle_html = middle_html.replace("{0}", format_date(deal_status.date_created)).replace("{1}", deal_status.deal.item_name).replace("{2}", deal_status.deal.place.name).replace("{3}", str(format(deal_status.deal.item_price, '.2f'))).replace("{4}", "1").replace("{5}", str(format(deal_status.deal.item_price, '.2f')))
        combined_middle_html = combined_middle_html + new_middle_html
    bottom_html = send_receipt_bottom_html
    top_html = top_html.format(format_date(last_successful_settlement), format_date(current_date))
    bottom_html = bottom_html.replace("{{promo_code}}", redeemed[0].user.profile.promo_code)
    combined_bottom_html = bottom_html.replace("{0}", str(format(total_cost, '.2f')))
    full_html = top_html + combined_middle_html + combined_bottom_html
    send_marketing_email("info@gethotspotapp.com", "Hotspot", [redeemed[0].user.email, "jazjit.singh@gmail.com"], "Hotspot Receipt", " ", full_html, "receipt")


def send_deals_retention_email(user):
    html = send_deals_retention_email_html

    html = html.replace("{{Promo Code}}", user.profile.promo_code)
    subject = "new Hotspot specials in your area"
    plaintext = send_deals_retention_email_plaintext
    plaintext = plaintext.replace("{{Promo Code}}", user.profile.promo_code)
    send_marketing_email("info@gethotspotapp.com", "Jared Jones", [user.email], subject, plaintext, html, "deals_retention")


def send_following_feature_email(user):
    html = send_following_feature_email_html
    newhtml = html.replace("{{promo code}}", user.profile.promo_code)
    plaintext = send_following_feature_email_plaintext
    newplaintext = plaintext.replace("{{promo code}}", user.profile.promo_code)
    send_marketing_email("info@gethotspotapp.com", "Jared Jones", [user.email], "Launching Hotspot Newsfeed", newplaintext, newhtml, "following feature launch")


def send_winback_email(user):
    html = send_winback_email_html
    month_from_now = datetime.now() + timedelta(days=31)
    two_weeks_string = format_date(month_from_now.date())
    html = html.replace('{{Expiration Date}}', two_weeks_string)
    plaintext = send_winback_email_plaintext
    plaintext = plaintext.replace('{{Expiration Date}}', two_weeks_string)
    if user.email != "" and user.email is not None:
        send_marketing_email("info@gethotspotapp.com", "Jared Jones", [user.email], "We've added a free drink to your account", plaintext, html, "winback email")


def send_error_report_email(subject, arr_errors):
        html = "errors: "
        for error in arr_errors:
            html = html + "<br>" + error
        send_marketing_email('william.xu@gethotspotapp.com', 'Will Xu', ['wxu121@gmail.com', 'jazjit.singh@gmail.com', 'jaredfoxjones@gmail.com'], subject, '', html, 'errors')


def send_user_interview_request(user):
    html = user_interview_request.replace('{{first_name}}', user.first_name)
    plaintext = user_interview_request_plain_text.replace('{{first_name}}', user.first_name)
    send_marketing_email("jas@gethotspotapp.com", "Jasjit Singh", [user.email], "Hotspot feedback", plaintext, html, "user_interview_request")


def send_weekly_sport_email(min_date=(datetime.now() - timedelta(weeks=1)), max_date=datetime.now()):
    emails = ["dougk@seastarrestaurant.com","clalley@seastarrestaurant.com","jared@gethotspotapp.com"]
    sport_deal = Deal.objects.get(place__name="Sport")
    redemptions = DealStatus.objects.filter(deal=sport_deal,deal_status="R",date_created__gte=min_date,date_created__lt=max_date)
    payout = len(redemptions)*sport_deal.item_cost
    subject_line = "Hotspot Weekly Report {0} to {1}".format(min_date.date(), max_date.date())
    html = """Hi Doug and Cathy,<br><br>This is your weekly automated Hotspot Report for {0} to {1}. We recorded {2} total first-drink redemptions, and have sent you a check for ${3}. Let us know if you have any questions! (Just hit 'reply' for Jared Jones).<br><br>Cheers,<br>Hotspot""".format(min_date.date(), max_date.date(), str(3), str(4.5))
    plaintext = "Hi Doug and Cathy,\n\nThis is your weekly automated Hotspot Report for {0} to {1}. We recorded {2} total first-drink redemptions, and have sent you a check for ${3}. Let us know if you have any questions! (Just hit 'reply' for Jared Jones).\n\nCheers,\nHotspot""".format(min_date.date(), max_date.date(), str(3), str(4.5))
    print plaintext
    terminal_answer = raw_input("Email these? y/n ").lower() == 'y'
    if terminal_answer is True:
        for email in emails:
            send_marketing_email("jared@gethotspotapp.com", "Hotspot", [email], subject_line, plaintext, html, "settlement_email")


def send_monthly_venue_report(venue,contact_name,contact_email,min_date,max_date,starting_inventory):
    deals = Deal.objects.filter(place=venue)
    redemptions = DealStatus.objects.filter(deal_status="R",deal__in=deals,date_created__gte=min_date,date_created__lt=max_date).exclude(user__in=excluded_users)
    favorites = Favorites.objects.filter(place=venue, active=True)
    unique_followers = favorites.values_list('user').distinct()
    notifications_sent = get_notifications_by_venue(venue, min_date, max_date)
    #page_views, unique_viewers = get_page_views_by_venue(venue, min_date, max_date)
    month = min_date.strftime('%B')
    revenue = 0
    for deal in deals:
        items = redemptions.filter(deal=deal)
        revenue = revenue + (len(items) * deal.item_cost)
    rev_string = str(revenue)[:-2]
    if len(redemptions) > 0:
        if starting_inventory>0:
            outstanding = starting_inventory - revenue
            if outstanding < 0:
                owed = revenue - starting_inventory
                payment_string = "we ran through the outstanding ${0} and sent you a check for ${1}".format(str(starting_inventory),str(owed))
            else:
                payment_string = "there is ${0} outstanding of the intial drink buy".format(str(outstanding))
        else:
            payment_string = "we sent you a check for ${0}".format(str(rev_string))
        html = first_drink_monthly_venue_email_html.replace('{{name}}',contact_name).replace('{{month}}',month).replace('{{redemptions}}',str(len(redemptions))).replace('{{venue}}',venue.name).replace('{{payment_string}}',payment_string).replace('{{invites}}',str(len(notifications_sent))).replace('{{followers}}',str(len(unique_followers)))
        plaintext = first_drink_monthly_venue_email_plaintext.replace('{{name}}', contact_name).replace('{{month}}', month).replace('{{redemptions}}', str(len(redemptions))).replace('{{venue}}', venue.name).replace('{{payment_string}}',payment_string).replace('{{invites}}', str(len(notifications_sent))).replace('{{followers}}', str(len(unique_followers)))
    elif len(redemptions) == 0:
        print "No redemptions for {0}".format(venue.name)
    subject_line = "Hotspot Monthly Report: {0}".format(month)
    print plaintext
    terminal_prompt = "Email {0}? y/n ".format(contact_email)
    terminal_answer = raw_input(terminal_prompt).lower() == 'y'
    if terminal_answer is True:
        send_marketing_email("jas@gethotspotapp.com", "Hotspot", [contact_email,"jas@gethotspotapp.com"], subject_line, plaintext, html, "monthly venue email")
    else:
        print "Didn't email {0}".format(venue.name)


def send_all_monthly_venue_reports(min_date, max_date,dct=first_drink_dict):
    active_deal_places = Deal.objects.filter(in_app_payment=True, active=True).values_list('place', flat=True)
    active_seattle_venues = DealPlace.objects.filter(pk__in=active_deal_places)
    for venue in active_seattle_venues:
        if venue.id == 20569:
            belltown = venue
            queen_anne = DealPlace.objects.get(id=20707)
            redemptions = DealStatus.objects.filter(deal_status="R", deal__place__in=[belltown,queen_anne], date_created__gte=min_date,date_created__lt=max_date).exclude(user__in=excluded_users)
            if len(redemptions) > 0:
                tot_inventory = dct[belltown.id]['inventory'] + dct[queen_anne.id]['inventory']
                send_monthly_venue_report(venue, dct[venue.id]['contact'], dct[venue.id]['contact_email'], min_date, max_date, tot_inventory)
        elif venue.id == 20707:
            print "Don't email Buckley's Queen Anne, combined into primary Buckley's"
        else:
            redemptions = DealStatus.objects.filter(deal_status="R", deal__place=venue, date_created__gte=min_date,date_created__lt=max_date).exclude(user__in=excluded_users)
            if len(redemptions) > 0:
                send_monthly_venue_report(venue,dct[venue.id]['contact'],dct[venue.id]['contact_email'],min_date,max_date,dct[venue.id]['inventory'])


def send_web_order_confirmation(cash_payment):
    email = cash_payment.email
    subject = "Order Confirmation"
    html_email, plaintext_email = get_web_order_emails(cash_payment)
    send_marketing_email("info@gehotspotapp.com", "Hotspot", [email], subject, plaintext_email, html_email, "web-confirmation")


def get_web_order_emails(cash_payment):
    if cash_payment.attendees == 1:
        tickets_purchased = "1 ticket"
    else:
        tickets_purchased = str(cash_payment.attendees) + " tickets"
    if cash_payment.tip:
        total = cash_payment.total + cash_payment.tip
    else:
        total = cash_payment.total
    total = '${:,.2f}'.format(total)
    html_email = web_order_confirmation_html.replace("{name}", cash_payment.name).replace("{total}", total).replace("{ticket_number_string}", tickets_purchased).replace("{venue_name}", cash_payment.event.place.name)
    plaintext_email = web_order_confirmation_plaintext.replace("{name}", cash_payment.name).replace("{total}", total).replace(
        "{ticket_number_string}", tickets_purchased).replace("{venue_name}", cash_payment.event.place.name)
    return html_email, plaintext_email


def send_app_order_confirmation(event_status):
    event = event_status.event
    subject = "Order Confirmation for {0} at {1}".format(event.item_name, event.place.name)
    plaintext_email = ""
    time_string = get_event_time(event)
    day_string = get_event_day(event)
    html_email = reservation_confirmation_email.replace("{0}", str(event.place.name)).replace("{1}", time_string).replace("{2}", day_string)
    user_email = event_status.user.email
    if user_email != "" and user_email is not None:
        send_marketing_email("rachael.olsen@gethotspotapp.com", "Hotspot", [user_email], subject, plaintext_email, html_email, subject)


# def get_event_time(event):
#     latitude = event.place.latitude
#     longitude = event.place.longitude
#     new_timezone = GeoTimeZone().get_timezone(latitude=latitude, longitude=longitude)
#     server_timezone = pytz.timezone(settings.TIME_ZONE)
#     localized_start_time = server_timezone.localize(event.start)
#     updated_start_time = localized_start_time.astimezone(tz=new_timezone)
#     localized_end_time = server_timezone.localize(event.end)
#     updated_end_time = localized_end_time.astimezone(tz=new_timezone)
#     return updated_start_time.strftime("%-I:%M%p") + "-" + updated_end_time.strftime("%-I:%M%p")

def get_timezone_for_event(event):
    lat = event.place.latitude
    lng = event.place.longitude
    # lat_range = [lat-1, lat+1]
    # lng_range = [lng-1, lng+1]
    # markets = Market.objects.filter(latitude__range=lat_range, longitude__range=lng_range)
    # market = get_nearest_market(lat, lng, markets)
    market = event.market
    if market:
        print "Market Found"
        return GeoTimeZone().get_python_timezone(market.timezone_id)
    else:
        print "Market Not Found"
        return GeoTimeZone().get_timezone(latitude=lat, longitude=lng)


def get_nearest_market(lat, lng, markets):
    current_distance = 100000
    closest_market = None
    for market in markets:
        dist = distance_between_two_points(lat, lng, market.latitude, market.longitude)
        if dist < current_distance:
            current_distance = dist
            closest_market = market
    return closest_market


def get_event_time(event):
    new_timezone = get_timezone_for_event(event)
    server_timezone = pytz.timezone(settings.TIME_ZONE)
    localized_start_time = server_timezone.localize(event.start)
    updated_start_time = localized_start_time.astimezone(tz=new_timezone)
    localized_end_time = server_timezone.localize(event.end)
    updated_end_time = localized_end_time.astimezone(tz=new_timezone)
    return updated_start_time.strftime("%-I:%M%p") + "-" + updated_end_time.strftime("%-I:%M%p")


def get_event_day(event):
    return event.start.strftime("%B %-d")


def send_event_marketing_email(user, sponsored_event, subject):
    date_string = get_event_day(sponsored_event)
    time_string = get_event_time(sponsored_event)
    unsubscribe_link = "{0}/unsubscribe/{1}/{2}/".format(settings.URL, user.email, sponsored_event.id)
    html_email = event_marketing_email.replace("{venue_image_url}", sponsored_event.place.image_url).replace("{venue_name}", sponsored_event.place.name).replace("{item_name}", sponsored_event.item_name).replace("{item_price}", "$" + str(int(sponsored_event.item_price))).replace("{presale_price}", "$" + str(int(sponsored_event.presale_item_price))).replace("{facebook_link}", sponsored_event.web_url).replace("{day_date_string}", date_string).replace("{time_string}", time_string).replace("{description}", sponsored_event.description).replace("{unsubscribe_link}", unsubscribe_link)
    plaintext = send_new_deal_email_plaintext
    if user.email != "" and user.email is not None:
        send_marketing_email("info@gethotspotapp.com", "Rachael Olsen", [user.email], subject, plaintext, html_email, subject)


def get_emails_for_event(event):
    emails = get_emails_for_market_without_date(event.market, event)
    blocked_emails = get_blocked_emails(event)
    return remove_blocked_emails(emails, blocked_emails)


def get_emails_for_market_without_users(market):
    cash_payment_emails = get_emails_from_cash_payment(market)
    submitted_emails = get_all_submitted_emails(market)
    all_emails = list(cash_payment_emails) + list(submitted_emails)
    filtered_emails = []
    for email in all_emails:
        filtered_emails.append(email.lower())
    return set(filtered_emails)


def remove_blocked_emails(all_emails, blocked_emails):
    updated_email_list = []
    for email in all_emails:
        if not email.lower() in blocked_emails:
            updated_email_list.append(email)
    return updated_email_list


def get_blocked_emails(event):
    unsubscribed_emails = EmailResponse.objects.filter(Q(status=EMAIL_STATUS.NOT_INTERESTED_IN_EVENT) | Q(status=EMAIL_STATUS.EVENT_UNSUBSCRIBE)).filter(event=event).values_list('email', flat=True)
    purchased_users = EventStatus.objects.filter(event=event, status="U").values_list('user', flat=True)
    purchased_tickets = User.objects.filter(pk__in=purchased_users).values_list('email', flat=True)
    all_emails = list(unsubscribed_emails) + list(purchased_tickets)
    filtered_emails = []
    for email in all_emails:
        filtered_emails.append(email.lower())
    return filtered_emails


def get_emails_for_day_of_reminder(event):
    events = SponsoredEvent.objects.filter(place=event.place)
    user_ids = EventStatus.objects.filter(event__in=events).values_list('user', flat=True)
    past_attendee_emails = User.objects.filter(pk__in=user_ids).values_list('email', flat=True)
    interested_emails = EmailResponse.objects.filter(event__in=events, status=EMAIL_STATUS.INTERESTED_IN_EVENT).values_list('email', flat=True)
    submitted_emails = Emails.objects.filter(event__in=events).values_list('email', flat=True)
    event_emails = list(set(list(interested_emails) + list(submitted_emails) + list(past_attendee_emails)))
    blocked_emails = get_blocked_emails(event)
    return remove_blocked_emails(event_emails, blocked_emails)


def get_emails_for_market_without_date(market, event=None):
    user_emails = get_emails_from_users(market, event)
    cash_payment_emails = get_emails_from_cash_payment(market)
    submitted_emails = get_all_submitted_emails(market)
    all_emails = list(user_emails) + list(cash_payment_emails) + list(submitted_emails)
    filtered_emails = []
    for email in all_emails:
        filtered_emails.append(email.lower())
    return set(filtered_emails)


def get_emails_from_users(market, event):
    users = get_user_within_distance(market.latitude, market.longitude, 40)
    user_ids_to_exclude = EventStatus.objects.filter(event=event, status="U").values_list('user', flat=True)
    users = users.exclude(pk__in=user_ids_to_exclude)
    emails = users.values_list('email', flat=True)
    return emails


def get_emails_from_cash_payment(market):
    places = get_venues_within_distance_for_events(market.latitude, market.longitude, 40)
    events = SponsoredEvent.objects.filter(place__in=places)
    emails = CashPayment.objects.filter(event__in=events, email__isnull=False).values_list('email', flat=True)
    return emails


def get_all_submitted_emails(market):
    emails = Emails.objects.filter(market=market).values_list('email', flat=True)
    return emails


def send_special_promotion_marketing_email(event, subject, description):
    emails = get_emails_for_event(event)
    for email in emails:
        send_special_event_marketing_email(email, event, description, subject)
    print str(len(emails)) + " emails sent for " + str(event.place.name)


def get_interested_link(email, event, response):
    return "{0}/email-response/{1}/{2}/{3}/".format(settings.URL, email, event.id, int(response))


def send_special_event_marketing_email(email, sponsored_event, description, subject, secondary_events=[]):
    date_string = get_event_day(sponsored_event)
    time_string = get_event_time(sponsored_event)
    category = subject + "-" + str(sponsored_event.id)
    venue_name = sponsored_event.place.name + " - " + sponsored_event.place.street_address + " (" + sponsored_event.market.name + ")"
    is_interested_link = get_interested_link(email, sponsored_event, True)
    is_not_interested_link = get_interested_link(email, sponsored_event, False)
    unsubscribe_link = "{0}/unsubscribe/{1}/{2}/".format(settings.URL, email, sponsored_event.id)
    description = description + '''<br><br><strong>Full Description</strong><br>''' + sponsored_event.description
    secondary_event_html = get_secondary_event_html(secondary_events)
    html_email = event_marketing_email.replace("{venue_image_url}", sponsored_event.place.image_url).replace("{venue_name}", venue_name).replace("{item_name}", sponsored_event.item_name).replace("{item_price}", "$" + str(int(get_current_app_price(sponsored_event)))).replace("{interested_link}", is_interested_link).replace("{not_interested_link}", is_not_interested_link).replace("{day_date_string}", date_string).replace("{time_string}", time_string).replace("{description}", description).replace("{unsubscribe_link}", unsubscribe_link).replace("{secondary_events}", secondary_event_html)
    plaintext = send_new_deal_email_plaintext
    if email != "" and email is not None:
        send_marketing_email("rachael.olsen@gethotspotapp.com", "Rachael Olsen", [email], subject, plaintext, html_email, category)


def get_secondary_event_html(secondary_events):
    if len(secondary_events) > 0:
        market = secondary_events[0].market
        html = top_of_secondary_events.replace('{market_name}', market.name)
        for event in secondary_events:
            event_price = "$" + str(int(get_current_app_price(event)))
            date_string = get_event_day(event)
            time_string = get_event_time(event)
            venue_name = event.place.name + " - " + event.place.street_address + " (" + event.market.name + ")"
            facebook_link = "http://www.facebook.com/" + str(event.facebook_event_id)
            new_html = body_of_secondary_event.replace("{item_name}", event.item_name).replace("{item_price}", event_price).replace("{venue_name}", venue_name).replace("{day_date_string}", date_string).replace("{time_string}", time_string).replace("{facebook_link}", facebook_link)
            html = html + new_html
        html = html + bottom_of_secondary_events
        return html
    else:
        return ""


def market_stats():
    markets = Market.objects.all()
    for market in markets:
        print market.name
    print ""
    for market in markets:
        emails = get_emails_for_market_without_date(market)
        print str(len(emails))
    print ""
    for market in markets:
        lat_range = [market.latitude - 1, market.latitude+1]
        lng_range = [market.longitude - 1, market.longitude + 1]
        events = []
        places_in_market = DealPlace.objects.filter(latitude__range=lat_range, longitude__range=lng_range).values_list('pk', flat=True)
        events_in_market = SponsoredEvent.objects.filter(place_id__in=places_in_market)
        for event in events_in_market:
            market_for_event = get_market_from_lat_lng(event.place.latitude, event.place.longitude)
            if market.id == market_for_event.id:
                events.append(event)
        unique_event_goers = EventStatus.objects.filter(event__in=events, status="R").values_list('user', flat=True)
        print str(len(set(unique_event_goers)))


def tickets_are_live(sponsored_event, is_test=True):
    subject = "New open bar tickets are live"
    description = '''Tickets are now live for our open bar at {0}. The first 30 people who buy tickets on the <a href="http://www.gethotspotapp.com">Hotspot app</a> will get their ticket for only $10. Make sure to reserve a spot ASAP!'''.format(sponsored_event.place.name)
    if is_test:
        emails = ["jazjit.singh@gmail.com"]
    else:
        emails = get_emails_for_event(sponsored_event)
    for email in emails:
        send_special_event_marketing_email(email, sponsored_event, description, subject)
    if not is_test:
        category = subject + "-" + str(sponsored_event.id)
        email_campaign = EmailCampaignTracker(event=sponsored_event, type=EMAIL_CAMPAIGN_TYPE.TICKETS_LIVE, subject=subject, description=description, total_sent=len(emails), category=category)
        email_campaign.save()
    print "Emails sent: " + str(len(emails))


def day_of_reminder(sponsored_event, is_test=True):
    subject = "Tonight - {0} at {1}".format(sponsored_event.item_name.lower() ,sponsored_event.place.name)
    description = '''Looking forward to seeing everyone tonight. We still have a few tickets left so make sure to reserve your spot on the <a href="http://www.gethotspotapp.com">Hotspot</a> app ASAP!'''
    if is_test:
        emails = ["jas@gethotspotapp.com"]
    else:
        emails = get_emails_for_day_of_reminder(sponsored_event)
        # emails = get_emails_for_event(sponsored_event)
    for email in emails:
        send_special_event_marketing_email(email, sponsored_event, description, subject)
    if not is_test:
        category = subject + "-" + str(sponsored_event.id)
        email_campaign = EmailCampaignTracker(event=sponsored_event, type=EMAIL_CAMPAIGN_TYPE.DAY_OF_EMAIL, subject=subject, description=description, total_sent=len(emails), category=category)
        email_campaign.save()
    print "Emails sent: " + str(len(emails))


def day_of_reminder_for_event(sponsored_event, is_test=True):
    subject = "Tonight - {0} at {1}".format(sponsored_event.item_name.lower() ,sponsored_event.place.name)
    description = '''Looking forward to seeing everyone tonight. We still have a few tickets left so make sure to reserve your spot on the <a href="http://www.gethotspotapp.com">Hotspot</a> app ASAP!'''
    if is_test:
        emails = ["jas@gethotspotapp.com"]
    else:
        emails = get_emails_for_day_of_reminder(sponsored_event)
        # emails = get_emails_for_event(sponsored_event)
    for email in emails:
        send_special_event_marketing_email(email, sponsored_event, description, subject)
    if not is_test:
        category = subject + "-" + str(sponsored_event.id)
        email_campaign = EmailCampaignTracker(event=sponsored_event, type=EMAIL_CAMPAIGN_TYPE.DAY_OF_EMAIL, subject=subject, description=description, total_sent=len(emails), category=category)
        email_campaign.save()
    print "Emails sent: " + str(len(emails))


def get_campaign_type(event):
    number_of_tickets_sold = get_event_count(event)
    early_bird_tickets_left = event.presale_cap - number_of_tickets_sold
    if early_bird_tickets_left > 10:
        return EMAIL_CAMPAIGN_TYPE.MORE_EARLY_BIRD_LEFT
    elif early_bird_tickets_left <= 10 and early_bird_tickets_left >= 0:
        return EMAIL_CAMPAIGN_TYPE.LESS_EARLY_BIRD_LEFT
    else:
        return EMAIL_CAMPAIGN_TYPE.REGULAR_LEFT


def get_event_count(event):
    e = EventStatus.objects.filter(event=event, status="U", refund_authorization__isnull=True)
    x = EventStatus.objects.filter(event=event, status="R", refund_authorization__isnull=True)
    c = CashPayment.objects.filter(event=event)
    attendees = 0
    for payment in c:
        attendees = payment.attendees + attendees
    return len(e) + len(x) + attendees


def send_event_emails(sponsored_event, subject, description, is_test=True):
    if is_test:
        emails = ["jazjit.singh@gmail.com"]
    else:
        emails = get_emails_for_event(sponsored_event)
    for email in emails:
        send_special_event_marketing_email(email, sponsored_event, description, subject)
    campaign_type = get_campaign_type(sponsored_event)
    if not is_test:
        category = subject + "-" + str(sponsored_event.id)
        email_campaign = EmailCampaignTracker(event=sponsored_event, type=campaign_type,
                                              subject=subject, description=description, total_sent=len(emails),
                                              category=category)
        email_campaign.save()
    print "Emails sent: " + str(len(emails))


def send_error_email(error):
    send_marketing_email("rachael.olsen@gethotspotapp.com", "Hotspot", ["jas@gethotspotapp.com"], "Error",
                         "", error, "Error email")


def get_market_from_lat_lng(lat, lng):
    lat_range = [lat - 1, lat + 1]
    lng_range = [lng - 1, lng + 1]
    markets = Market.objects.filter(latitude__range=lat_range, longitude__range=lng_range)
    market = get_nearest_market(lat, lng, markets)
    return market
