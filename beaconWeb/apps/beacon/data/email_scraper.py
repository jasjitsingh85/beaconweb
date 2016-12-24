from bs4 import BeautifulSoup
import requests
import requests.exceptions
from urlparse import urlsplit
from collections import deque
import re
from beaconWeb.apps.beacon.models.place_contact import PlaceContact
from beaconWeb.apps.beacon.models.deal_place import DealPlace
from beaconWeb.apps.beacon.common.constants.place_contact_type import PLACE_CONTACT_TYPE
from beaconWeb.apps.beacon.data.place_scraper import get_possible_event_venues
import csv

def extract_email_from_websites(websites):
    print websites
    # a queue of urls to be crawled
    new_urls = deque(websites)
    # a set of urls that we have already crawled
    processed_urls = set()
    # a set of crawled emails
    emails = set()
    # process urls one by one until we exhaust the queue
    print "NEW URLS: " + str(new_urls)
    count = 0
    while len(new_urls):
        # move next url from the queue to the set of processed urls
        url = new_urls.popleft()
        processed_urls.add(url)
        # extract base url to resolve relative links
        parts = urlsplit(url)
        base_url = "{0.scheme}://{0.netloc}".format(parts)
        path = url[:url.rfind('/')+1] if '/' in parts.path else url
        # get url's content
        print("Processing %s" % url)
        try:
            response = requests.get(url, timeout=20)
        except Exception,e:
            print str(e)
            # ignore pages with errors
            continue
        # extract all email addresses and add them into the resulting set
        new_emails = set(re.findall(r"[a-z0-9\.\-+_]+@[a-z0-9\.\-+_]+\.[a-z]+", response.text, re.I))
        emails.update(new_emails)
        # create a beutiful soup for the html document
        soup = BeautifulSoup(response.text)
        # find and process all the anchors in the document
        for anchor in soup.find_all("a"):
            # extract link url from the anchor
            link = anchor.attrs["href"] if "href" in anchor.attrs else ''
            # resolve relative links
            if link.startswith('/'):
                link = base_url + link
            elif not link.startswith('http'):
                link = path + link
            # add the new url to the queue if it was not enqueued nor processed yet
            if not link in new_urls and not link in processed_urls and check_link(link):
                new_urls.append(link)
        count += 1
        if count == 20:
            break
    return emails


def check_link(link):
    excluded = ['facebook', 'twitter', 'instagram', 'proxy', 'yelp', '.jpg', '.png', '.pdf']
    if any(x in link for x in excluded):
        return False
    else:
        return True


def get_emails_from_websites(venues):
    venues_with_email = []
    for venue in venues:
        venue_obj = venue
        venue_obj['emails'] = extract_email_from_websites([venue['url']])
        venues_with_email.append(venue_obj)
        print str(venues_with_email)
    return venues_with_email


def venues_to_csv(venues):
    for venue in venues:
        if len(venue['emails']) > 0:
            emails = list(venue['emails'])
            excluded_strings = ['.png', '.css', '.jpg' ]
            for email in emails:
                if not any(x in email for x in excluded_strings):
                    print venue['name'].title() + ',' + email + ','


def scrape_for_place_contact(deal_places):
    excluded_strings = ['.png', '.css', '.jpg']
    domains = ['gmail', 'yahoo', 'hotmail', 'aol', 'comcast', 'mac', 'msn', 'sbc', 'bellsouth', 'verizon', 'earthlink', 'cox', 'rediff', 'btinternet', 'charter', 'shaw', 'ntlworld']
    for deal_place in deal_places:
        print "ID: ", deal_place.id
        try:
            emails = extract_email_from_websites([deal_place.website])
            emails = list(emails)
            if emails:
                for upper_email in emails:
                    email = upper_email.lower()
                    print email
                    if not any(x in email for x in excluded_strings):
                        if within(deal_place.website.lower(), email):
                            print "GREAT: ", email
                            save_place_contact(deal_place, email)
                        else:
                            if any(x in email for x in domains):
                                print "GREAT: ", email
                                save_place_contact(deal_place, email)
        except:
            print "error"
            continue


def save_place_contact(place, email):
    if not PlaceContact.objects.filter(email=email).exists() and len(email) < 40:
        place_contact = PlaceContact(email=email, place=place, type=PLACE_CONTACT_TYPE.SCRAPE)
        #place_contact = PlaceContact(email=email, place=place)
        place_contact.save()


def within(website, email):
    if 'https' in website and 'www' in website:
        if website[12:19] in email:
            return True
    elif 'http' in website and 'www' in website:
        if website[11:18] in email:
            return True
    elif 'https' in website:
        if website[8:14] in email:
            return True
    elif 'http' in website:
        if website[7:13] in email:
            return True
    else:
        if website[4:11] in email:
            return True
    return False


def scrape_emails_for_event_venues_in_city(latitude, longitude, radius):
    event_venues = get_possible_event_venues(latitude, longitude, radius)
    to_scrape = []
    for event_venue in event_venues:
        if event_venue.website:
            to_scrape.append(event_venue)
    scrape_for_place_contact(to_scrape)