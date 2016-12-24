import urllib
import urllib2
import oauth2
import json
import time
from beaconWeb.apps.beacon.models.deal_place import DealPlace
from beaconWeb.apps.beacon.models.raw_place import RawPlace
from beaconWeb.apps.beacon.retention.emails import send_marketing_email, send_error_report_email
from beaconWeb.apps.beacon.data.common_scraper_utils import get_lat_and_lng_pairs, cities, boundingBox, get_places_in_radius
from beaconWeb.common_utils import normalize_phone_number
from yelpapi import YelpAPI
import traceback

YELP_CONSUMER_KEY = "r9jQDGwVieQ6sJhFIj4iqw"
YELP_CONSUMER_SECRET = "gpwpuZdo3qZjoqSCA1OED9yj99s"
YELP_TOKEN = "UGK-9Zx1Xq0jQXG-hTT45725bgPIe-4J"
YELP_TOKEN_SECRET = "E6qND5nVSMAnGfYIQRH7w4UZP-M"

YELP_CONSUMER_KEY2 = "sYcTXxukics-aEORT15KKw"
YELP_CONSUMER_SECRET2 = "jvjMiltJg8iy4QytZzaM2e4TX9M"
YELP_TOKEN2 = "i2CrJfSUJbk_ajSNl260aO0_3iTS2o6f"
YELP_TOKEN_SECRET2 = "JH5vyesVIj8nmFBP9V7rC1vgCFE"

YELP_CONSUMER_KEY3 = "VjmD6qg-sqwLrmlvqd3ccA"
YELP_CONSUMER_SECRET3 = "T_GCB3mJ2UWGh-lqTj_bz9t-CEQ"
YELP_TOKEN3 = "	bEhg4bZ2yewwL55xKY5NKNja-Yhkr_Zd"
YELP_TOKEN_SECRET3 = "hMPvks_sCEzFScU8Z-D49alYpn4"


def add_places_from_yelp_for_all_cities():
    for city in cities:
        add_places_from_yelp(cities[city]['latitude'], cities[city]['longitude'], cities[city]['radius'], 10)


def add_places_from_yelp(lat, lng, radius, increments):
    latitudes, longitudes = get_lat_and_lng_pairs(lat, lng, radius, increments)
    terms = ["bar", "happy hour", "nightclub", "concert", "tavern", "brewery", "hookah", "pub", "beer", "wine", "cocktail", "sake"]
    # terms = [ "beer", "wine", "cocktail", "sake", "burgers", "grill"]
    category_filters = ["nightlife", "active", "arts"]
    for term in terms:
        scrape_and_add_places_from_yelp(latitudes, longitudes, term)
    for category in category_filters:
        scrape_and_add_places_from_yelp(latitudes, longitudes, None, category)


def search_with_yelp(term, category_filter, lat, lng, offset):
    lat_lng = str(lat) + ',' + str(lng)
    yelp_api = YelpAPI(YELP_CONSUMER_KEY, YELP_CONSUMER_SECRET, YELP_TOKEN, YELP_TOKEN_SECRET)
    search_results = yelp_api.search_query(ll=lat_lng, term=term, category_filter=category_filter, radius_filter=2000, offset=offset, limit=20)
    return search_results['businesses']


def request(host, path, url_params=None):
    url_params = url_params or {}
    url = 'http://{0}{1}?'.format(host, urllib.quote(path.encode('utf8')))
    consumer = oauth2.Consumer(YELP_CONSUMER_KEY, YELP_CONSUMER_SECRET)
    oauth_request = oauth2.Request(method="GET", url=url, parameters=url_params)
    oauth_request.update(
        {
            'oauth_nonce': oauth2.generate_nonce(),
            'oauth_timestamp': oauth2.generate_timestamp(),
            'oauth_token': YELP_TOKEN,
            'oauth_consumer_key': YELP_CONSUMER_KEY
        }
    )
    token = oauth2.Token(YELP_TOKEN, YELP_TOKEN_SECRET)
    oauth_request.sign_request(oauth2.SignatureMethod_HMAC_SHA1(), consumer, token)
    signed_url = oauth_request.to_url()
    print u'Querying {0} ...'.format(url)
    conn = urllib2.urlopen(signed_url, None)
    try:
        response = json.loads(conn.read())
    finally:
        conn.close()
    return response


def get_business(business_id):
    API_HOST = 'api.yelp.com'
    BUSINESS_PATH = '/v2/business/'
    new_business_path = BUSINESS_PATH + business_id
    return request(API_HOST, new_business_path)


def search_yelp(lat, lng):
    lat_lng = str(lat) + ',' + str(lng)
    API_HOST = 'api.yelp.com'
    SEARCH_PATH = '/v2/search/'
    url_params = {
        'category_filter': 'nightlife, All',
        'sort': 1,
        'radius_filter': 5000,
        'cll': lat_lng,
    }
    return request(API_HOST, SEARCH_PATH, url_params=url_params)

def get_yelp_ids(places=DealPlace.objects.filter(latitude__range=(47.5, 47.73), longitude__range=(-122.43, -122.24))):
    for deal in places:
        if not deal.yelp_id:
            bounds = str(deal.latitude - .001) + ',' + str(deal.longitude - .001) + '|' + str(deal.latitude + .001) + ',' + str(deal.longitude + .001)
            venues = search(deal.name.encode('ascii', 'ignore'), bounds)
            if venues['businesses']:
                deal.yelp_id = venues['businesses'][0]['id']
                deal.save()
                print venues['businesses'][0]['id']

def get_all_bars():
    newbars = []
    xdelta = (47.73 - 47.5)/2
    ydelta = (122.43-122.24)/2
    lowerx = 47.5
    lowery = -122.43
    for x in range(0, 2):
        for y in range(0, 2):
            xlowerbound = lowerx + (x * xdelta)
            xupperbound = lowerx + ((x + 1) * xdelta)
            ylowerbound = lowery + (y * ydelta)
            yupperbound = lowery + ((y + 1) * ydelta)
            bounds = str(xlowerbound) + ',' + str(ylowerbound) + '|' + str(xupperbound) + ',' + str(yupperbound)
            print bounds
            print len(newbars)
            for offset in range(0, 1000, 20):
                print len(newbars)
                try:
                    results = search('happy hour', bounds, offset)
                except:
                    print "limit reached", offset
                    continue
                for result in results['businesses']:
                    newbars.append(result['id'])
    return newbars


def remove_duplicate_bars(bars):
    unique_bars = []
    bar_ids = []
    for bar in bars:
        if bar['id'] not in bar_ids:
            unique_bars.append(bar)
            bar_ids.append(bar['id'])
    nonredundant = []
    for each in unique_bars:
        if not DealPlace.objects.filter(yelp_id=each['id']).exists(): 
            nonredundant.append(each)
    return nonredundant


def get_yelp_ratings(deal_places):
    places_with_yelp_id = deal_places.filter(yelp_id__isnull=False)
    for each in places_with_yelp_id:
        try:
            yelp_venue = get_business(each.yelp_id)
            if yelp_venue['rating_img_url_large']:
                each.yelp_rating_image_url = yelp_venue['rating_img_url_large']
                each.save()
            elif yelp_venue['rating_img_url']:
                each.yelp_rating_image_url = yelp_venue['rating_img_url']
                each.save()
            elif yelp_venue['rating_img_url_small']:
                each.yelp_rating_image_url = yelp_venue['rating_img_url_small']
                each.save()
            if yelp_venue['review_count']:
                each.yelp_review_count = yelp_venue['review_count']
                each.save()
        except:
            print "failed on " + each.yelp_id
            continue

def add_yelp_ratings_for_city(latitude, longitude, radius):
    places = get_places_in_radius(latitude, longitude, radius, False)
    get_yelp_ratings(places)


def add_deal_place_from_raw_venue(venue):
    if not RawPlace.objects.filter(yelp_id=venue['id']).exists():
        name = venue['name']
        yelp_id = venue['id']
        if 'coordinate' in venue['location']:
            longitude = venue['location']['coordinate']['longitude']
            latitude = venue['location']['coordinate']['latitude']
        else:
            longitude = 0.0
            latitude = 0.0
        if 'neighborhoods' in venue['location']:
            neighborhood = venue['location']['neighborhoods'][0]
        else:
            neighborhood = ""
        if len(venue['location']['address']) > 0:
            street_address = venue['location']['address'][0]
        else:
            street_address = ""
        if 'phone' in venue:
            phone = normalize_phone_number(venue['phone'])
        else:
            phone = ""
        place_type = ""
        place_description = ""
        raw_place = RawPlace(longitude=longitude, latitude=latitude, name=name, street_address=street_address, phone=phone, yelp_id=yelp_id,
                              place_description=place_description, place_type=place_type, neighborhood=neighborhood)
        raw_place.save()


def add_DealPlace_from_yelp(bar_ids):
    failed=[]
    for each in bar_ids:
        try:
            venue = get_business(each)
            if venue['review_count'] > 5:
                longitude = venue['location']['coordinate']['longitude']
                latitude = venue['location']['coordinate']['latitude']
                name = venue['name']
                street_address = venue['location']['address'][0]
                yelp_id = venue['id']
                phone = venue['phone']
                place_description = ''
                dealplace = DealPlace(longitude=longitude, latitude=latitude, name=name, street_address=street_address, phone=phone, yelp_id=yelp_id, place_description=place_description)
                dealplace.save()
        except:
            failed.append(each)
            continue
    return failed


def scrape_and_add_places_from_yelp(latitudes, longitudes, term=None, category_filter=None):
    for lat in latitudes:
        for lng in longitudes:
            print str(lat) + " " + str(lng)
            print str(term)
            print str(category_filter)
            count = 0
            while count < 50:
                time.sleep(4)
                search_results = search_with_yelp(term, category_filter, lat, lng, 20 * count)
                if len(search_results) > 0:
                    for result in search_results:
                        add_deal_place_from_raw_venue(result)
                    count += 1
                else:
                    print "Limit reached " + str(20 * (count - 1))
                    count = 51


def close_venues_for_all_cities():
    for city in cities:
        close_venues_in_city(cities[city]['latitude'], cities[city]['longitude'], cities[city]['radius'])


def close_venues_in_city(latitude, longitude, radius):
    latitude_min, longitude_min, latitude_max, longitude_max = boundingBox(latitude, longitude, radius)
    places = DealPlace.objects.filter(latitude__range=(latitude_min, latitude_max), longitude__range=(longitude_min, longitude_max), yelp_id__isnull=False, in_review=False)
    closed_venues = []
    for each in places:
        try:
            venue = get_business(each.yelp_id)
            if venue['is_closed']:
                each.closed = True
                each.save()
                closed_string = 'Closed: ' + str(each.name)
                closed_venues.append(closed_string)
        except Exception:
            traceback.print_exc()
    print "Close venues successful"
    send_error_report_email("Closed Venues", closed_venues)