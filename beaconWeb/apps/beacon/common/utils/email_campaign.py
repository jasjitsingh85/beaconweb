from beaconWeb.apps.beacon.models.sponsored_event import SponsoredEvent
from beaconWeb.apps.beacon.models.emails import Emails
from beaconWeb.apps.beacon.models.event_status import EventStatus
from beaconWeb.apps.beacon.models.cash_payment import CashPayment
from beaconWeb.apps.beacon.models.market import Market
from beaconWeb.settings import RQ_THREAD
from beaconWeb.apps.beacon.common.common_utils import get_next_event_in_market
from datetime import datetime, timedelta
from beaconWeb.apps.beacon.models.email_campaign_tracker import EmailCampaignTracker
from beaconWeb.apps.beacon.analytics.updated_analytics import get_user_within_distance
from beaconWeb.apps.beacon.common.constants.email_campaign_type import EMAIL_CAMPAIGN_TYPE
from beaconWeb.apps.beacon.classes.event_sorter import EventSorter
from beaconWeb.apps.beacon.retention.emails import get_emails_for_event, send_event_emails, tickets_are_live, get_emails_for_market_without_users, send_special_event_marketing_email, get_campaign_type


from django_rq import job
import random

is_test = True

lots_of_early_bird_tickets_left = [ {"subject":"Open bar early-bird tickets almost sold out", "description":'''The first 30 tickets sell for only $10. There are still tickets left at this price for Saturday's event so make sure to reserve your spot ASAP on the <a href="http://www.gethotspotapp.com">Hotspot</a> app!'''},
                                    {"subject":"Open bar early-bird tickets are almost gone", "description":'''The first 30 tickets sell for only $10. There are still tickets left at this price - make sure to reserve your spot ASAP on the <a href="http://www.gethotspotapp.com">Hotspot</a> app!'''},
                                    {"subject":"Early-bird tickets for open bar this week", "description":'''There are still early-bird ($10) tickets left for the open bar this week. Hope you can make it! Just make sure to reserve your spot on the <a href="http://www.GetHotspotApp.com">Hotspot app</a>!'''}
                                   ]

some_early_bird_tickets_left = [{"subject": "Open bar early-bird tickets almost sold out",
                                    "description": '''The first 30 tickets sell for only $10. There are still tickets left at this price for Saturday's event so make sure to reserve your spot ASAP on the <a href="http://www.gethotspotapp.com">Hotspot</a> app!'''},
                                   {"subject": "Open bar early-bird tickets are almost gone",
                                    "description": '''The first 30 tickets sell for only $10. There are still tickets left at this price - make sure to reserve your spot ASAP on the <a href="http://www.gethotspotapp.com">Hotspot</a> app!'''},
                                   {"subject": "Early-bird tickets for open bar this week",
                                    "description": '''There are still early-bird ($10) tickets left for the open bar this week. Hope you can make it! Just make sure to reserve your spot on the <a href="http://www.GetHotspotApp.com">Hotspot app</a>!'''}
                                   ]

no_early_bird_tickets_left = [{"subject": "Tickets for open bar",
                                    "description": '''There are still tickets left for this open bar event. Hope you can make it! Just make sure to reserve your spot on the <a href="http://www.GetHotspotApp.com">Hotspot app</a>!'''}
                                   ]


@job(RQ_THREAD)
def check_and_run_weekly_tickets_are_live_email(is_test=True, markets_to_exclude=[]):
    markets = Market.objects.all()
    tickets_not_live = []
    for market in markets:
        event = get_next_event_in_market(market)
        if event and event.start < datetime.now() + timedelta(weeks=5) and not EmailCampaignTracker.objects.filter(type=EMAIL_CAMPAIGN_TYPE.TICKETS_LIVE, event=event).exists():
            tickets_not_live.append(event)
    for event in tickets_not_live:
        tickets_are_live(event, is_test)


def check_and_run_this_weeks_emails(is_test=True):
    markets = Market.objects.all()
    events_this_week = []
    for market in markets:
        event = get_next_event_in_market(market)
        if event and EmailCampaignTracker.objects.filter(type=EMAIL_CAMPAIGN_TYPE.TICKETS_LIVE, event=event).exists():
            if event.start < datetime.now()+timedelta(weeks=1):
                events_this_week.append(event)
    for event in events_this_week:
        subject = "Open bar at {0} on {1}".format(event.place.name, datetime.strftime(event.start, "%A"))
        description = '''Make sure to reserve your spot on the <a href="http://www.GetHotspotApp.com">Hotspot app</a>!'''
        send_event_emails(event, subject, description, is_test)


def check_and_run_weekly_reminder_email(is_test=True):
    markets = Market.objects.all().exclude(pk=1)
    other_events = []
    for market in markets:
        event = get_next_event_in_market(market)
        if event and EmailCampaignTracker.objects.filter(type=EMAIL_CAMPAIGN_TYPE.TICKETS_LIVE, event=event).exists():
            if not event.start < datetime.now()+timedelta(weeks=1) and event.start < datetime.now() + timedelta(weeks=5):
                if event not in other_events:
                    other_events.append(event)
    for event in other_events:
        subject, description = get_subject_and_description(event)
        send_event_emails(event, subject, description, is_test)


def get_users_in_all_markets():
    markets = Market.objects.all()
    users_in_event_markets = []
    for market in markets:
        users = get_user_within_distance(market.latitude, market.longitude)
        users_in_event_markets.extend(users)
        users_in_event_markets = list(set(users_in_event_markets))
    return users_in_event_markets

# def check_and_run_specialized_weekly_reminder_email(is_test=True):
#     event_market_ids = SponsoredEvent.objects.filter(start__gte=datetime.now(), start__lte=datetime.now()+timedelta(weeks=6)).values_list('market', flat=True)
#     event_markets = Market.objects.filter(pk__in=event_market_ids)
#     users_in_event_markets = []
#     for market in event_markets:
#         users = get_user_within_distance(market.latitude, market.longitude)
#         users_in_event_markets.extend(users)
#         users_in_event_markets = list(set(users_in_event_markets))
#         # user_ids_to_exclude = EventStatus.objects.filter(event=event, status="U").values_list('user', flat=True)
#         # users = users.exclude(pk__in=user_ids_to_exclude)
#     for market in event_markets:
#         send_generic_market_email(market, is_test)
#     send_specialized_email(users_in_event_markets)


def send_generic_market_email(market, is_test):
    sponsored_event = get_next_event_in_market(market)
    event = get_next_event_in_market(market)
    campaign_type = get_campaign_type(event)
    subject, description = get_subject_and_description(event)
    if is_test:
        emails = ["jazjit.singh@gmail.com"]
    else:
        emails = get_emails_for_market_without_users(market)
    for email in emails:
        send_special_event_marketing_email(email, event, description, subject)
        category = subject + "-" + str(sponsored_event.id)
        email_campaign = EmailCampaignTracker(event=sponsored_event, type=campaign_type,
                                              subject=subject, description=description, total_sent=len(emails),
                                              category=category)
        email_campaign.save()


# def send_specialized_email(users):
#     for user in users:
#         event = select_best_event_for_user(user)
#         subject, description = get_subject_and_description(event)
#         campaign_type = get_campaign_type(event)
#         send_special_event_marketing_email(user.email, event, description, subject)
#         category = subject + "-" + str(event.id)
#         email_campaign = EmailCampaignTracker(event=event, type=campaign_type,
#                                               subject=subject, description=description, total_sent=1,
#                                               category=category, user=user)
#         email_campaign.save()

#
# def select_best_event_for_user(user):
#     events = SponsoredEvent.objects.filter(start__gte=datetime.now(), start__lte=datetime.now()+timedelta(weeks=6))
#     user_locations = Location.objects.filter(user=user, date_created__gte=datetime.now() - timedelta(weeks=24))
#     purchase_events = EventStatus.objects.filter(user=user).filter(Q(status=EVENT_STATUS.REDEEMED) | Q(status=EVENT_STATUS.GOING))
#     for location in user_locations:
#         for event in events:
#             distance = distance_between_two_points(event.place.latitude, event.place.longitude, location.latitude, location.longitude)
#             event.score = event.score + distance
#     for event in events:
#         event.score = event.score/float(len(user_locations))
#     for _event in purchase_events:
#         for event in events:
#             distance = distance_between_two_points(_event.place.latitude, _event.place.longitude, event.place.latitude,
#                                                    event.place.longitude)
#             event.score = event.score - (10 * distance)
#     # TODO return event with lowest event score


# def send_event_emails_for_market(market, is_test=True):
#     if is_test:
#         emails = ["jazjit.singh@gmail.com"]
#     else:
#         emails = get_emails_for_market_without_users(market)
#     send_generic_market_email(emails, market)
#     print "Emails sent: " + str(len(emails))


def run_emails_chron_for_users():
    users = get_users_in_all_markets()
    for user in users:
        primary_event, secondary_events = EventSorter().order_events_for_user_in_market(user)
        if primary_event:
            if primary_event.start > datetime.now() and primary_event.start < datetime.now()+timedelta(weeks=1):
                subject = "{0} at {1} on {2}".format(primary_event.item_name, primary_event.place.name, datetime.strftime(primary_event.start, "%A"))
                description = '''Make sure to reserve your spot on the <a href="http://www.GetHotspotApp.com">Hotspot app</a>!'''
                send_special_event_marketing_email(user.email, primary_event, description, subject, secondary_events)
                category = subject + "-" + str(primary_event.id)
                email_campaign = EmailCampaignTracker(event=primary_event, user=user, type=EMAIL_CAMPAIGN_TYPE.WEEK_OF_EMAIL,
                                                  subject=subject, description=description, total_sent=1,
                                                  category=category)
                email_campaign.save()
            else:
                if EmailCampaignTracker.objects.filter(event=primary_event, user=user, type=EMAIL_CAMPAIGN_TYPE.TICKETS_LIVE).exists():
                    subject, description = get_subject_and_description(primary_event)
                    send_special_event_marketing_email(user.email, primary_event, description, subject, secondary_events)
                    category = subject + "-" + str(primary_event.id)
                    campaign_type = get_campaign_type(primary_event)
                    email_campaign = EmailCampaignTracker(event=primary_event, user=user, type=campaign_type,
                                                          subject=subject, description=description, total_sent=1,
                                                          category=category)
                    email_campaign.save()
                else:
                    subject = "New open bar tickets are live"
                    description = '''Tickets are now live for our open bar at {0}. The first 30 people who buy tickets on the <a href="http://www.gethotspotapp.com">Hotspot app</a> will get their ticket for only $10. Make sure to reserve a spot ASAP!'''.format(
                        primary_event.place.name)
                    send_special_event_marketing_email(user.email, primary_event, description, subject, secondary_events)
                    category = subject + "-" + str(primary_event.id)
                    email_campaign = EmailCampaignTracker(event=primary_event, user=user, type=EMAIL_CAMPAIGN_TYPE.TICKETS_LIVE,
                                                          subject=subject, description=description, total_sent=1,
                                                          category=category)
                    email_campaign.save()


def run_emails_chron_for_emails():
    emails = Emails.objects.all().distinct('email')
    for email_obj in emails:
        primary_event, secondary_events = EventSorter().order_events_for_email_in_market(email_obj)
        if primary_event:
            if primary_event.start > datetime.now() and primary_event.start < datetime.now()+timedelta(weeks=1):
                subject = "{0} at {1} on {2}".format(primary_event.item_name, primary_event.place.name, datetime.strftime(primary_event.start, "%A"))
                description = '''Make sure to reserve your spot on the <a href="http://www.GetHotspotApp.com">Hotspot app</a>!'''
                send_special_event_marketing_email(email_obj.email, primary_event, description, subject, secondary_events)
                category = subject + "-" + str(primary_event.id)
                email_campaign = EmailCampaignTracker(event=primary_event, email=email_obj, type=EMAIL_CAMPAIGN_TYPE.WEEK_OF_EMAIL,
                                                  subject=subject, description=description, total_sent=1,
                                                  category=category)
                email_campaign.save()
            else:
                if EmailCampaignTracker.objects.filter(event=primary_event, email=email_obj, type=EMAIL_CAMPAIGN_TYPE.TICKETS_LIVE).exists():
                    subject, description = get_subject_and_description(primary_event)
                    send_special_event_marketing_email(email_obj.email, primary_event, description, subject, secondary_events)
                    category = subject + "-" + str(primary_event.id)
                    campaign_type = get_campaign_type(primary_event)
                    email_campaign = EmailCampaignTracker(event=primary_event, email=email_obj, type=campaign_type,
                                                          subject=subject, description=description, total_sent=1,
                                                          category=category)
                    email_campaign.save()
                else:
                    subject = "New open bar tickets are live"
                    description = '''Tickets are now live for our open bar at {0}. The first 30 people who buy tickets on the <a href="http://www.gethotspotapp.com">Hotspot app</a> will get their ticket for only $10. Make sure to reserve a spot ASAP!'''.format(
                        primary_event.place.name)
                    send_special_event_marketing_email(email_obj.email, primary_event, description, subject, secondary_events)
                    category = subject + "-" + str(primary_event.id)
                    email_campaign = EmailCampaignTracker(event=primary_event, email=email_obj, type=EMAIL_CAMPAIGN_TYPE.TICKETS_LIVE,
                                                          subject=subject, description=description, total_sent=1,
                                                          category=category)
                    email_campaign.save()


def run_emails_chron_for_cash_payment_emails():
    cash_payments = CashPayment.objects.all().distinct('email')
    for cash_payment in cash_payments:
        primary_event, secondary_events = EventSorter().order_events_for_cash_payment_in_market(cash_payment)
        if primary_event:
            if primary_event.start > datetime.now() and primary_event.start < datetime.now()+timedelta(weeks=1):
                subject = "{0} at {1} on {2}".format(primary_event.item_name, primary_event.place.name, datetime.strftime(primary_event.start, "%A"))
                description = '''Make sure to reserve your spot on the <a href="http://www.GetHotspotApp.com">Hotspot app</a>!'''
                send_special_event_marketing_email(cash_payment.email, primary_event, description, subject, secondary_events)
                category = subject + "-" + str(primary_event.id)
                email_campaign = EmailCampaignTracker(event=primary_event, cash_payment=cash_payment, type=EMAIL_CAMPAIGN_TYPE.WEEK_OF_EMAIL,
                                                  subject=subject, description=description, total_sent=1,
                                                  category=category)
                email_campaign.save()
            else:
                if EmailCampaignTracker.objects.filter(event=primary_event, cash_payment=cash_payment, type=EMAIL_CAMPAIGN_TYPE.TICKETS_LIVE).exists():
                    subject, description = get_subject_and_description(primary_event)
                    send_special_event_marketing_email(cash_payment.email, primary_event, description, subject, secondary_events)
                    category = subject + "-" + str(primary_event.id)
                    campaign_type = get_campaign_type(primary_event)
                    email_campaign = EmailCampaignTracker(event=primary_event, cash_payment=cash_payment, type=campaign_type,
                                                          subject=subject, description=description, total_sent=1,
                                                          category=category)
                    email_campaign.save()
                else:
                    subject = "New open bar tickets are live"
                    description = '''Tickets are now live for our open bar at {0}. The first 30 people who buy tickets on the <a href="http://www.gethotspotapp.com">Hotspot app</a> will get their ticket for only $10. Make sure to reserve a spot ASAP!'''.format(
                        primary_event.place.name)
                    send_special_event_marketing_email(cash_payment.email, primary_event, description, subject, secondary_events)
                    category = subject + "-" + str(primary_event.id)
                    email_campaign = EmailCampaignTracker(event=primary_event, cash_payment=cash_payment, type=EMAIL_CAMPAIGN_TYPE.TICKETS_LIVE,
                                                          subject=subject, description=description, total_sent=1,
                                                          category=category)
                    email_campaign.save()



@job(RQ_THREAD)
def check_and_run_day_of_email():
    pass
    #day before email


def get_subject_and_description(event):
    number_of_tickets_sold = get_event_count(event)
    early_bird_tickets_left = event.presale_cap - number_of_tickets_sold
    if early_bird_tickets_left > 10:
        email_obj = random.choice(lots_of_early_bird_tickets_left)
        return email_obj['subject'], email_obj['description']
    elif early_bird_tickets_left <= 10 and early_bird_tickets_left >= 0:
        email_obj = random.choice(some_early_bird_tickets_left)
        return email_obj['subject'], email_obj['description']
    else:
        email_obj = random.choice(no_early_bird_tickets_left)
        return email_obj['subject'], email_obj['description']


def get_event_count(event):
    e = EventStatus.objects.filter(event=event, status="U", refund_authorization__isnull=True)
    x = EventStatus.objects.filter(event=event, status="R", refund_authorization__isnull=True)
    c = CashPayment.objects.filter(event=event)
    attendees = 0
    for payment in c:
        attendees = payment.attendees + attendees
    return len(e) + len(x) + attendees