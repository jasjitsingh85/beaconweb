from beaconWeb.apps.beacon.data.yelp_scraper import add_places_from_yelp, close_venues_in_city, add_yelp_ratings_for_city
from beaconWeb.apps.beacon.data.place_scraper import match_and_add_places_from_raw_places, auto_approve_event_venues, delete_duplicate_places_for_new_city, auto_approve_new_deal_places_for_city
from beaconWeb.apps.beacon.data.website_scraper import scrape_websites
from beaconWeb.apps.beacon.data.foursquare_scraper import add_foursquare_extras_for_new_city, add_foursquare_ids_for_new_city
from beaconWeb.apps.beacon.data.facebook_scraper import add_facebook_ids_for_new_city, add_facebook_extras_for_new_city
from beaconWeb.apps.beacon.data.happy_hour_scraper import scrape_happy_hours, integrate_happy_hours_for_city
from beaconWeb.apps.beacon.data.email_scraper import scrape_emails_for_event_venues_in_city

def launch_new_city(latitude, longitude, radius):
    add_places_from_yelp(latitude, longitude, radius, 10)
    match_and_add_places_from_raw_places(latitude, longitude, radius)
    delete_duplicate_places_for_new_city(latitude, longitude, radius)
    scrape_happy_hours(latitude, longitude, radius, 10)
    integrate_happy_hours_for_city(latitude, longitude, radius)
    close_venues_in_city(latitude, longitude, radius)
    add_yelp_ratings_for_city(latitude, longitude, radius)
    add_foursquare_ids_for_new_city(latitude, longitude, radius)
    add_foursquare_extras_for_new_city(latitude, longitude, radius)
    auto_approve_new_deal_places_for_city(latitude, longitude, radius)
    #auto_approve_event_venues(latitude, longitude, radius)
    add_facebook_ids_for_new_city(latitude, longitude, radius)
    add_facebook_extras_for_new_city(latitude, longitude, radius)
    scrape_websites(latitude, longitude, radius)
    scrape_emails_for_event_venues_in_city(latitude, longitude, radius)

