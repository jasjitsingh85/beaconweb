from bs4 import BeautifulSoup
from django.contrib.auth.models import User
import requests
import requests.exceptions
from urlparse import urlsplit
from collections import deque
import urllib2
from dateutil import parser
from beaconWeb.apps.beacon.models import DealPlace, SyndicatedEvents, Favorites
from datetime import datetime, timedelta
import re
import pytz
from beaconWeb.settings import TIME_ZONE
from beaconWeb.apps.beacon.common.constants.event_type import EVENT_TYPE
import facebook
import traceback

timezone = pytz.timezone(TIME_ZONE)


def get_events_for_user(user):
    favorite_places = Favorites.objects.filter(active=True, user=user).values_list('place', flat=True)
    # print "Favorite Places: " + str(favorite_places)
    # sponsored_events = list(SyndicatedEvents.objects.filter(event_type=EVENT_TYPE.SPONSORED, start__gte=datetime.now()-timedelta(hours=6), start__lte=datetime.now()+timedelta(weeks=2)).order_by('start'))
    events = list(SyndicatedEvents.objects.filter(event_type=EVENT_TYPE.FACEBOOK, place_id__in=favorite_places, start__gte=datetime.now()-timedelta(hours=6), start__lte=datetime.now()+timedelta(weeks=2)).order_by('start'))
    # combined_events = sponsored_events + events
    # print "Events (in function): " + str(events)
    return events


def get_new_venues_to_scrape():
    venues = order_venues_by_followers()
    print "New Venues to Triage"
    for venue in venues:
        if venue['number_of_followers'] >= 5:
            print str(venue['deal_place_id']) + " " + str(venue['name']) + " " + str(venue['website'])
    print ""


def adjust_to_server_timezone(datetime_to_adjust):
    updated_datetime = datetime_to_adjust.replace(second=0, microsecond=0) + timedelta(hours=2)
    return updated_datetime


def daily_event_scrape():
    get_new_venues_to_scrape()
    ballroom()
    bad_alberts()
    q_nightclub()
    moe_bar()
    # can_can()


def add_event(place, title, date, event_id):
    link = "https://www.facebook.com/events/" + str(event_id)
    syndicated_event = SyndicatedEvents(place=place, title=title, event_id=event_id,  website=link, start=date)
    syndicated_event.save()


def update_event(place, title, date, event_id):
    syndicated_event = SyndicatedEvents.objects.get(event_id=event_id)
    syndicated_event.title = title
    syndicated_event.date = date
    syndicated_event.place = place
    syndicated_event.save()

def clear_deals(place):
    events = SyndicatedEvents.objects.filter(place=place)
    events.delete()
#nectar lounge parser


def get_venues_with_favorites():
    venue_ids = Favorites.objects.all().values_list('place', flat=True)
    venues = DealPlace.objects.filter(pk__in=venue_ids).exclude(pk__in=active_scrapers_at_deal_places).exclude(pk__in=unscrapable_venues)
    return venues


def order_venues_by_followers():
    venues = get_venues_with_favorites()
    updated_venues = []
    for venue in venues:
        new_venue = {}
        new_venue['number_of_followers'] = len(Favorites.objects.filter(place=venue))
        new_venue['name'] = venue.name
        new_venue['website'] = venue.website
        new_venue['deal_place_id'] = venue.id
        updated_venues.append(new_venue)
    updated_venues.sort(key=lambda x: x['number_of_followers'], reverse=True)
    return updated_venues


active_scrapers_at_deal_places = [100, 107, 29107, 29107, 112]
unscrapable_venues = [99,20178,20095,20715, 29114, 20218, 113, 97, 102, 92, 115, 104, 103, 94, 95, 109, 91, 29110, 110, 29112, 116, 108, 20419, 29115, 20106, 29077, 29113, 20103, 29070, 29039, 29064, 20245, 20250, 20433, 20967,
                      20870, 20303, 29075, 20908, 20601, 20123, 20286, 20117, 20111, 20176, 20066, 20108, 29083, 20414, 20388, 20336, 20469]


# Event Scrapers
def parse_url(url_to_parse):
    url = url_to_parse
    content = urllib2.urlopen(url).read()
    soup = BeautifulSoup(content)
    return soup

def parse_private_url(url_to_parse):
    hdr = {'User-Agent': 'Mozilla/5.0'}
    req = urllib2.Request(url_to_parse, headers=hdr)
    page = urllib2.urlopen(req)
    soup = BeautifulSoup(page)
    return soup

#venue event scrapers


def ballroom():
    place = DealPlace.objects.get(pk=100)
    soup = parse_url(place.events_url)
    clear_deals(place)
    all_events = soup.find_all('article', class_="eventlist-event--upcoming")
    for event in all_events:
        try:
            title = event.find('a', class_='eventlist-title-link').text
            # print title
            date = event.find('time', class_="event-time-24hr-start").get('datetime')
            time = event.find('time', class_="event-time-24hr-start").text
            stripped_date = datetime.strptime(date + " " + time,"%Y-%m-%d %H:%M")
            # print stripped_date
            link = event.find('a', class_="eventlist-title-link").get('href')
            link = "http://www.ballroomfremont.com" + link
            # print link
            add_event(place, title, adjust_to_server_timezone(stripped_date), link)
        except:
            print "Event Scrape Failure: " + place.name


def bad_alberts():
    place = DealPlace.objects.get(pk=107)
    soup = parse_url(place.events_url)
    clear_deals(place)
    all_events = soup.find_all('div', class_="type-tribe_events")
    for event in all_events:
        try:
            title = event.h2.a.get('title')
            # print title
            date = event.find('span', class_="value-title").get('title')
            stripped_date = datetime.strptime(date,"%Y-%m-%dUTC%I:%M") + timedelta(hours=12)
            # print stripped_date
            link = event.find('div', class_="tribe-events-list-event-description").a.get('href')
            # print link
            add_event(place, title, adjust_to_server_timezone(stripped_date), link)
        except:
            print "Event Scrape Failure: " + place.name


def q_nightclub():
    place = DealPlace.objects.get(pk=29107)
    soup = parse_url(place.events_url)
    clear_deals(place)
    all_events = soup.find_all('span', class_="day-wrapper")
    for event in all_events:
        try:
            title = event.find('div', class_='caption').a.text
            if title is not None:
                # print title
                date = event.parent['class'][1]
                time = event.find('p', class_="date").text.strip()
                stripped_date = datetime.strptime(date + " " + time,"date-%Y%m%d %I:%M %p")
                # print stripped_date
                link = event.find('a', class_="get-tickets").get('href')
                # print link
                add_event(place, title, adjust_to_server_timezone(stripped_date), link)
        except:
            print "Event Scrape Failure: " + place.name


def moe_bar():
    place = DealPlace.objects.get(pk=112)
    soup = parse_private_url(place.events_url)
    clear_deals(place)
    all_events = soup.find_all('div', class_="rhino-event-wrapper")
    for event in all_events:
        try:
            title = event.find('div', class_="rhino-event-info").a.text.strip()
            # print title
            date = str(datetime.now().year) + " " + event.find('div', class_="rhino-event-datebox-month").p.text + " " + event.find('div', class_="rhino-event-datebox-date").p.text
            time = event.find('p', class_="rhino-event-time").text
            stripped_date = datetime.strptime(date + " " + time,"%Y %b %d %I:%M %p")
            # print stripped_date
            link = event.find('a', class_="rhino-event-more-info").get('href')
            # print link
            add_event(place, title, adjust_to_server_timezone(stripped_date), link)
        except:
            print "Event Scrape Failure: " + place.name


def can_can():
    place = DealPlace.objects.get(pk=106)
    soup = parse_private_url(place.events_url)
    clear_deals(place)
    all_events = soup.find_all('div', class_="pl-item")
    for event in all_events:
        try:
            title = event.find('h3', class_="pl-name").text
            print title
            date = event.time.get('datetime')
            # stripped_date = datetime.strptime(date + " " + time,"%Y %b %d %I:%M %p")
            print date
            link = event.find('a', class_="rhino-event-more-info").get('href')
            print link
            # add_event(place, title, adjust_to_server_timezone(stripped_date), link)
        except:
            print "Event Scrape Failure: " + place.name
