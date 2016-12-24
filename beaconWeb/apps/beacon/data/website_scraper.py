import re
from bs4 import BeautifulSoup
import mechanize
import urlparse
import time, random
from beaconWeb.apps.beacon.models.deal_place import DealPlace
from beaconWeb.common_utils import smart_format, remove_non_ascii
import csv
import traceback
from beaconWeb.apps.beacon.data.common_scraper_utils import boundingBox, cities, get_places_in_radius


def scrape_websites_for_all_cities():
    for city in cities:
        scrape_websites(cities[city]['latitude'], cities[city]['longitude'], cities[city]['radius'])


def scrape_websites(latitude, longitude, radius):
    count = 1
    places = get_places_in_radius(latitude, longitude, radius, False)
    places = places.filter(website__isnull=True)
    br = mechanize.Browser(factory=mechanize.RobustFactory())
    br.set_handle_robots(False)
    br.set_handle_equiv(False)
    br.addheaders = [('User-agent', 'Mozilla/5.0')]
    for place in places:
        try:
            print count
            wt = random.uniform(1, 2)
            time.sleep(wt)
            br.open( "http://google.com" )
            br.select_form( 'f' )
            br.form[ 'q' ] = remove_non_ascii(place.name) + "seattle wa"
            data = br.submit()
            soup = BeautifulSoup(data.read())
            num = 0
            while num < 3:
                url = urlparse.parse_qs(urlparse.urlparse(soup.select('.r a')[num]['href']).query)['q'][0]
                strings_to_exclude = ['plus.google', 'yelp', 'facebook','urbanspoon', 'foursquare', 'zomato', 'tripadvisor', 'allmenus', 'thestranger', 'seattlemet', 'thrillist', 'seattle.eater', 'yahoo','capitolhillseattle', 'eventful', 'groupon', 'clubplanet', 'postfastr', 'opentable', 'menupix', 'menuism', 'letzgoout', 'barmano', '2findlocal', 'whitepages', 'manta', 'gigsounds', 'mapquest', 'www.restaurant.com', 'nochelatina']
                if 'http' in url and not any(string in url for string in strings_to_exclude):
                    place.website = url
                    place.save()
                    break
                num += 1
            count += 1
        except Exception:
            traceback.print_exc()
    print "Scrape websites successful"