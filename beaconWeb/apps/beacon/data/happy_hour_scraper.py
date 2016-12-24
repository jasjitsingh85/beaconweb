from mechanize import Browser
from bs4 import BeautifulSoup as BS
import requests
import requests.exceptions
from urlparse import urlsplit
from beaconWeb.apps.beacon.models.raw_happy_hour import RawHappyHour
from beaconWeb.apps.beacon.models.deal_place import DealPlace
from beaconWeb.apps.beacon.models.syndicated_deal import SyndicatedDeal
from beaconWeb.apps.beacon.data.common_scraper_utils import get_lat_and_lng_pairs, cities, boundingBox
from datetime import datetime, timedelta
import re
import ast
import json
import time
import boto.mturk.connection
from django.conf import settings
from itertools import chain
from fuzzywuzzy import fuzz
from fuzzywuzzy import process

sandbox_host = 'mechanicalturk.sandbox.amazonaws.com'
real_host = 'mechanicalturk.amazonaws.com'


mturk = boto.mturk.connection.MTurkConnection(
    aws_access_key_id = settings.AWS_ACCESS_KEY_ID,
    aws_secret_access_key = settings.AWS_SECRET_ACCESS_KEY,
    host = real_host,
    debug = 1 # debug = 2 prints out all requests. but we'll just keep it at 1
)


def import_happy_hours_from_mturk():
    auto_reject_incorrect_hits()
    auto_approve_correct_hits()


def auto_approve_correct_hits():
    hits = mturk.get_all_hits()
    hits_list = list(chain(hits))
    for hit in hits_list:
        assignments = mturk.get_assignments(hit.HITId)
        submitted_assignments = []
        for assignment in assignments:
            if assignment.AssignmentStatus == "Submitted":
                submitted_assignments.append(assignment)
        if len(submitted_assignments) == 2:
            check_assignments(submitted_assignments)


def check_assignments(assignments):
    print ""
    for assignment in assignments:
        description = assignment.answers[0][0].fields[0]
        print description
    print str(fuzz.token_sort_ratio(assignments[0].answers[0][0].fields[0], assignments[1].answers[0][0].fields[0]))

#Mech Turk
def auto_reject_incorrect_hits():
    hits = mturk.get_all_hits()
    hits_list = list(chain(hits))
    for hit in hits_list:
        assignments = mturk.get_assignments(hit.HITId)
        for assignment in assignments:
            if assignment.AssignmentStatus == "Submitted":
                basic_assignment_validation(assignment)


def basic_assignment_validation(assignment):
    happy_hour_description = assignment.answers[0][0].fields[0]
    excluded_website_terms = ['.pdf', 'http', 'www']
    excluded_time_terms = ['p.m.', 'a.m.', ' pm', ' am', '0pm', '1pm', '2pm', '3pm', '4pm', '5pm', '6pm', '7pm', '8pm', '9pm', '0am', '1am', '2am', '3am', '4am', '5am', '6am', '7am', '8am', '9am']
    if happy_hour_description == "":
        message = "You cannot leave the first happy hour info field blank as per the instructions. You must submit with either the happy hour description of 'None' if none can be found on the website."
        reject_assignment(assignment, message)
        print "DESCRIPTION: " + assignment.answers[0][0].fields[0]
    elif any(string in happy_hour_description.lower() for string in excluded_website_terms):
        message = "You cannot put url's into the happy hour description field. The description must conform to the examples as laid out in the instructions."
        reject_assignment(assignment, message)
        print "DESCRIPTION: " + assignment.answers[0][0].fields[0]
    elif any(string in happy_hour_description for string in excluded_time_terms):
        message = "You cannot put day or times into the happy hour description field. These must be sumitted in the day and time fields."
        reject_assignment(assignment, message)
        print "DESCRIPTION: " + assignment.answers[0][0].fields[0]
    elif len(happy_hour_description) < 5 and happy_hour_description.lower() != "none":
        message = "You must put None if there is no happy hour."
        reject_assignment(assignment, message)
        print "DESCRIPTION: " + happy_hour_description


def reject_assignment(assignment, feedback):
    mturk.reject_assignment(assignment.AssignmentId, feedback)


# Happy Hour App Scrapers
def get_multiple_venues_for_happy_hours(raw_happy_hours):
    raw_happy_hours = raw_happy_hours.exclude(description=None)
    for raw_happy_hour in raw_happy_hours:
        deal_place = match_deal_place(raw_happy_hour)
        # if deal_place > 1:
        #     print "add place" + str(raw_happy_hour.name)

def integrate_happy_hours_for_city(latitude, longitude, radius):
    latitude_min, longitude_min, latitude_max, longitude_max = boundingBox(latitude, longitude, radius)
    raw_happy_hours = RawHappyHour.objects.filter(latitude__range=(latitude_min, latitude_max), longitude__range=(longitude_min, longitude_max))
    integrate_happy_hours(raw_happy_hours)


def integrate_happy_hours(raw_happy_hours):
    raw_happy_hours = raw_happy_hours.exclude(description=None)
    for raw_happy_hour in raw_happy_hours:
        deal_place = match_deal_place(raw_happy_hour)
        if deal_place is None:
            print "add place" + str(raw_happy_hour.name)
            add_deal_place_and_happy_hour(raw_happy_hour)
        elif len(deal_place) == 1:
            print "updated " + str(deal_place[0].name)
            update_happy_hour(deal_place[0], raw_happy_hour)


def add_deal_place_and_happy_hour(raw_happy_hour):
    place = DealPlace()
    place.latitude = raw_happy_hour.latitude
    place.longitude = raw_happy_hour.longitude
    place.name = raw_happy_hour.name
    if raw_happy_hour.company_description:
        place.place_description = raw_happy_hour.company_description
    else:
        place.place_description = ""
    place.street_address = raw_happy_hour.street
    place.phone = raw_happy_hour.phone
    place.website = raw_happy_hour.website
    place.in_review = True
    place.save()
    add_happy_hour_from_raw_data(raw_happy_hour, place)


def update_happy_hour(place, raw_happy_hour):
    if SyndicatedDeal.objects.filter(place=place).exclude(is_verified=True, date_updated__gte=datetime.now()-timedelta(weeks=24)).exists():
        existing_happy_hours = SyndicatedDeal.objects.filter(place=place).exclude(is_verified=True, date_updated__gte=datetime.now()-timedelta(weeks=24)).exclude(date_updated__gte=datetime.now()-timedelta(hours=1))
        existing_happy_hours.delete()
        add_happy_hour_from_raw_data(raw_happy_hour, place)


def add_happy_hour_from_raw_data(raw_happy_hour, place):
    description = get_raw_description(raw_happy_hour)
    start = get_time_in_seconds(raw_happy_hour.start_time)
    end = get_time_in_seconds(raw_happy_hour.end_time)
    days = get_days(raw_happy_hour.days)
    print days
    syndicated_deal = SyndicatedDeal.objects.create(place=place, description=description, start=start, end=end, days=days)

def get_days_active(raw_days):
    days_array = ast.literal_eval(raw_days)
    print days_array
    days = SyndicatedDeal.days_active
    day_bits = [days.Sunday, days.Monday, days.Tuesday, days.Wednesday, days.Thursday, days.Friday, days.Saturday, days.Sunday]
    bitfield = 0
    if "sun" in days_array:
        bitfield = bitfield | day_bits[0]
    if "mon" in days_array:
        bitfield = bitfield | day_bits[1]
    if "tue" in days_array:
        bitfield = bitfield | day_bits[2]
    if "wed" in days_array:
        bitfield = bitfield | day_bits[3]
    if "thu" in days_array:
        bitfield = bitfield | day_bits[4]
    if "fri" in days_array:
        bitfield = bitfield | day_bits[5]
    if "sat" in days_array:
        bitfield = bitfield | day_bits[6]
    return bitfield
    #return '{0:07b}'.format(bitfield)[::-1]


def get_days(raw_days):
    days_array = ast.literal_eval(raw_days)
    print days_array
    days = SyndicatedDeal.days_active
    day_bits = [days.Sunday, days.Monday, days.Tuesday, days.Wednesday, days.Thursday, days.Friday, days.Saturday, days.Sunday]
    days = ""
    if "sun" in days_array:
        days += "1"
    else:
        days += "0"
    if "mon" in days_array:
        days += "1"
    else:
        days += "0"
    if "tue" in days_array:
        days += "1"
    else:
        days += "0"
    if "wed" in days_array:
        days += "1"
    else:
        days += "0"
    if "thu" in days_array:
        days += "1"
    else:
        days += "0"
    if "fri" in days_array:
        days += "1"
    else:
        days += "0"
    if "sat" in days_array:
        days += "1"
    else:
        days += "0"
    return days


def get_time_in_seconds(time_string):
    hours_and_minutes = time_string.split(":")
    hours = int(hours_and_minutes[0])
    minutes = int(hours_and_minutes[1])
    seconds = (hours * 60 * 60) + (minutes * 60)
    return seconds


def get_raw_description(raw_happy_hour):
    if raw_happy_hour.description.isupper():
        return raw_happy_hour.description.title()
    else:
        return raw_happy_hour.description


#Happy Hour Integration
def match_deal_place(raw_happy_hour):
    #filter first by lat lng
    if raw_happy_hour.street and DealPlace.objects.filter(street_address__icontains=raw_happy_hour.street).exists():
        # print "Street Match: " + raw_happy_hour.name
        try:
            return [DealPlace.objects.get(street_address__icontains=raw_happy_hour.street)]
        except:
            # print "MULTIPLE VENUES: " + str(raw_happy_hour.street) + " " + str(raw_happy_hour.name)
            print "MULTIPLE VENUES: " + str(raw_happy_hour.street) + " " + str(raw_happy_hour.name)
    elif DealPlace.objects.filter(latitude=raw_happy_hour.latitude, longitude=raw_happy_hour.longitude).exists():
        # print "Lat Lng Match: " + raw_happy_hour.name
        try:
            return [DealPlace.objects.get(latitude=raw_happy_hour.latitude, longitude=raw_happy_hour.longitude)]
        except:
            # print "MULTIPLE VENUES: " + str(raw_happy_hour.latitude) + " " + str(raw_happy_hour.name)
            print "MULTIPLE VENUES: " + str(raw_happy_hour.latitude) + " " + str(raw_happy_hour.name)
    elif raw_happy_hour.phone and DealPlace.objects.filter(phone__icontains=raw_happy_hour.phone).exists():
        # print "Phone Match: " + str(raw_happy_hour.name)
        try:
            return [DealPlace.objects.get(phone__icontains=raw_happy_hour.phone)]
        except:
            # print "MULTIPLE VENUES: " + str(raw_happy_hour.phone) + " " + str(raw_happy_hour.name)
            print "MULTIPLE VENUES: " + str(raw_happy_hour.phone) + " " + str(raw_happy_hour.name)
    elif raw_happy_hour.website and DealPlace.objects.filter(website__icontains=raw_happy_hour.website).exists():
        # print "Website Match: " + raw_happy_hour.name
        try:
            return [DealPlace.objects.get(website__icontains=raw_happy_hour.website)]
        except:
            # print "MULTIPLE VENUES: " + str(raw_happy_hour.website) + " " + str(raw_happy_hour.name)
            print "MULTIPLE VENUES: " + str(raw_happy_hour.website) + " " + str(raw_happy_hour.name)
    else:
        print "Not Found" + " " + str(raw_happy_hour.name)
        return None
    return []

def scrape_happy_hours_for_all_cities():
    for city in cities:
        scrape_happy_hours(cities[city]['latitude'], cities[city]['longitude'], cities[city]['radius'], 10)


#Happy Hour Scraper
def scrape_happy_hours(lat, lng, radius, increments):
    latitudes, longitudes = get_lat_and_lng_pairs(lat, lng, radius, increments)
    base_url = "http://api.villagevoice.com//mobileapi/search/type:happyhour/"
    url_string = "day:{0}/sort:distance/platform:ios/lat:{1}/lng:{2}/page:{3}"
    days = ["mon", "wed", "fri", "sun"]
    for day in days:
        for lat in latitudes:
            for lng in longitudes:
                try:
                    page = 0
                    has_data = True
                    while has_data:
                        url = base_url + url_string.format(day, lat, lng, page)
                        json = get_json_response(url)
                        if json:
                            happy_hour_data = json['sections'][3]['data']
                            if len(happy_hour_data) > 0:
                                for happy_hour in happy_hour_data:
                                    add_or_update_raw_happy_hour(happy_hour)
                            else:
                                has_data = False
                        else:
                            has_data = False
                        page += 1
                        time.sleep(0.1)
                except:
                    continue


def add_or_update_raw_happy_hour(happy_hour):
    info_id = int(happy_hour['infogroup_id'])
    if RawHappyHour.objects.filter(gt_id=info_id).exists():
        raw_happy_hour = RawHappyHour.objects.get(gt_id=info_id)
    else:
        raw_happy_hour = RawHappyHour()
        raw_happy_hour.gt_id = info_id
    if 'city' in happy_hour:
        raw_happy_hour.city = happy_hour['city']
    if 'company_description' in happy_hour:
        raw_happy_hour.company_description = happy_hour['company_description']
    if 'cuisine_label' in happy_hour:
        raw_happy_hour.cuisine_label = happy_hour['cuisine_label']
    if 'longitude' in happy_hour:
        raw_happy_hour.longitude = happy_hour['longitude']
    if 'latitude' in happy_hour:
        raw_happy_hour.latitude = happy_hour['latitude']
    if 'name' in happy_hour:
        raw_happy_hour.name = happy_hour['name']
    if 'phone' in happy_hour:
        raw_happy_hour.phone = happy_hour['phone']
    if 'street' in happy_hour:
        raw_happy_hour.street = happy_hour['street']
    if 'website' in happy_hour:
        raw_happy_hour.website = happy_hour['website']
    if 'days' in happy_hour:
        raw_happy_hour.days = happy_hour['days']
    if 'start_time' in happy_hour:
        raw_happy_hour.start_time = happy_hour['start_time']
    if 'end_time' in happy_hour:
        raw_happy_hour.end_time = happy_hour['end_time']
    if 'description' in happy_hour:
        raw_happy_hour.description = happy_hour['description']
    if 'active' in happy_hour:
        raw_happy_hour.active = happy_hour['active']
    raw_happy_hour.save()


def get_json_response(url):
    print("Processing %s" % url)
    try:
        response = requests.get(url)
        return json.loads(response.text)
    except:
        print "FAILED:" + str(url)
        return None