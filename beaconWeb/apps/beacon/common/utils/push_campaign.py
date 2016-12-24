from django.contrib.auth.models import User
from beaconWeb.apps.beacon.analytics.updated_analytics import get_user_within_distance
from beaconWeb.apps.beacon.tasks.send_sms import send_hotspot_push
from beaconWeb.apps.beacon.models.email_campaign_tracker import EmailCampaignTracker
from beaconWeb.apps.beacon.models.event_status import EventStatus
from beaconWeb.apps.beacon.models.market import Market
from beaconWeb.apps.beacon.models.push_campaign_tracker import PushCampaignTracker
from beaconWeb.apps.beacon.common.constants.push_campaign_type import PUSH_CAMPAIGN_TYPE
from beaconWeb.apps.beacon.common.common_utils import get_next_event_in_market
from beaconWeb.apps.beacon.common.utils.tracker import track_notification
from datetime import datetime, timedelta
from beaconWeb.apps.beacon.common.constants.email_campaign_type import EMAIL_CAMPAIGN_TYPE
from beaconWeb.settings import RQ_THREAD
from django_rq import job


@job(RQ_THREAD)
def tickets_are_live_push_notifications(is_test=True):
    markets = Market.objects.all()
    upcoming_events = []
    for market in markets:
        event = get_next_event_in_market(market)
        if event and not PushCampaignTracker.objects.filter(type=PUSH_CAMPAIGN_TYPE.TICKETS_LIVE, event=event).exists():
            upcoming_events.append(event)
    for event in upcoming_events:
        body = "Tickets are now live for the {0} at {1}. There are a limited number available for ${2} so reserve yours soon!".format(event.item_name.lower(), event.place.name, int(event.presale_item_price))
        if is_test:
            print event.place.name
            user = User.objects.get(username="5413359388")
            send_hotspot_push([user], body, None, None, None, event.id)
        else:
            all_users = get_user_within_distance(event.place.latitude, event.place.longitude)
            users_ids_to_exclude = EventStatus.objects.filter(event=event, status="U").values_list('user', flat=True)
            users = all_users.exclude(pk__in=users_ids_to_exclude)
            print "Event: " + event.place.name + " " + str(len(users))
            count = 0
            for user in users:
                send_hotspot_push([user], body, None, None, None, event.id)
                track_notification(user, "DP", body)
                count += 1
            push_campaign = PushCampaignTracker(event=event, message=body, total_sent=count, type=PUSH_CAMPAIGN_TYPE.TICKETS_LIVE)
            push_campaign.save()


def send_individual_push_for_tickets_live():
    campaigns = EmailCampaignTracker.objects.filter(type=EMAIL_CAMPAIGN_TYPE.TICKETS_LIVE, date_sent__gte=datetime.now()-timedelta(days=3), user__isnull=False)
    for campaign in campaigns:
        user = campaign.user
        event = campaign.event
        body = "Tickets are now live for the {0} at {1}. There are a limited number available for ${2} so reserve yours soon!".format(event.item_name.lower(), event.place.name, int(event.presale_item_price))
        send_hotspot_push([user], body, None, None, None, event.id)
        track_notification(user, "DP", body)