from beaconWeb.apps.beacon.models.sponsored_event import SponsoredEvent
from beaconWeb.apps.beacon.models.market import Market
from datetime import datetime, timedelta
from django.db.models import Q
from beaconWeb.apps.beacon.common.constants.event_status import EVENT_STATUS
from beaconWeb.apps.beacon.models.event_status import EventStatus
from beaconWeb.apps.beacon.models.location import Location
from beaconWeb.common_utils import distance_between_two_points


class EventSorter(object):

    def get_primary_market(self, user):
        markets = Market.objects.all()
        purchase_events = EventStatus.objects.filter(user=user).filter(
            Q(status=EVENT_STATUS.REDEEMED) | Q(status=EVENT_STATUS.GOING))
        user_locations = Location.objects.filter(user=user).order_by('-date_created')[:50]
        if not user_locations and not purchase_events:
            return None
        for market in markets:
            market.score = 0
        if user_locations:
            for location in user_locations:
                for market in markets:
                    distance = distance_between_two_points(market.latitude, market.longitude, location.latitude,
                                                           location.longitude)
                    market.score = market.score + distance
                for market in markets:
                    market.score = market.score / float(len(user_locations))
        if purchase_events:
            for market in markets:
                total_distance = 0
                for event_status in purchase_events:
                    distance = distance_between_two_points(event_status.event.place.latitude,
                                                           event_status.event.place.longitude,
                                                           market.latitude,
                                                           market.longitude)
                    total_distance = total_distance + distance
                market.score = market.score + (total_distance/float(len(purchase_events)))
        markets = list(markets)
        markets.sort(key=lambda x: x.score)
        return markets[0]
    def order_events_for_user_in_market(self, user, weeks=6):
        market = self.get_primary_market(user)
        lat_range = [market.latitude - .3, market.latitude + .3]
        lng_range = [market.longitude - .3, market.longitude + .3]
        events = SponsoredEvent.objects.filter(start__gte=datetime.now(),
                                       start__lte=datetime.now() + timedelta(weeks=weeks), market=market)
        if len(events) == 0:
            return None, None
        user_locations = Location.objects.filter(user=user, latitude__range=lat_range, longitude__range=lng_range).order_by('-date_created')[:50]
        purchase_events = EventStatus.objects.filter(user=user, event__in=events).filter(
            Q(status=EVENT_STATUS.REDEEMED) | Q(status=EVENT_STATUS.GOING))
        for event in events:
            event.score = 0
        if user_locations:
            for location in user_locations:
                for event in events:
                    distance = distance_between_two_points(event.place.latitude, event.place.longitude, location.latitude,
                                                           location.longitude)
                    event.score = event.score + distance
            for event in events:
                event.score = event.score / float(len(user_locations))
        if purchase_events:
            for event in events:
                total_distance = 0
                for event_status in purchase_events:
                    distance = distance_between_two_points(event_status.event.place.latitude, event_status.event.place.longitude,
                                                           event.place.latitude,
                                                           event.place.longitude)
                    total_distance = total_distance + distance
                event.score = event.score + (total_distance/float(len(purchase_events)))
        events = list(events)
        events.sort(key=lambda x: x.score)
        primary_event = events[0]
        secondary_events = SponsoredEvent.objects.filter(pk__in=[item.pk for item in events]).exclude(pk=primary_event.id).order_by('start')
        return primary_event, secondary_events
    def order_events_for_email_in_market(self, email, weeks=6):
        market = email.market
        # lat_range = [market.latitude - .3, market.latitude + .3]
        # lng_range = [market.longitude - .3, market.longitude + .3]
        events = SponsoredEvent.objects.filter(start__gte=datetime.now(),
                                               start__lte=datetime.now() + timedelta(weeks=weeks), market=market).order_by('start')
        if len(events) == 0:
            return None, None
        primary_event = events[0]
        secondary_events = SponsoredEvent.objects.filter(pk__in=[item.pk for item in events]).exclude(
            pk=primary_event.id).order_by('start')
        return primary_event, secondary_events

    def order_events_for_cash_payment_in_market(self, cash_payment, weeks=6):
        market = cash_payment.event.market
        # lat_range = [market.latitude - .3, market.latitude + .3]
        # lng_range = [market.longitude - .3, market.longitude + .3]
        events = SponsoredEvent.objects.filter(start__gte=datetime.now(),
                                               start__lte=datetime.now() + timedelta(weeks=weeks),
                                               market=market).order_by('start')
        if len(events) == 0:
            return None, None
        primary_event = events[0]
        secondary_events = SponsoredEvent.objects.filter(pk__in=[item.pk for item in events]).exclude(
            pk=primary_event.id).order_by('start')
        return primary_event, secondary_events
