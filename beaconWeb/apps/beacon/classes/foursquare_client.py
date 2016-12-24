import foursquare
from beaconWeb.settings import FOURSQUARE_CLIENT_ID, FOURSQUARE_CLIENT_SECRET


class FoursquareClient:
    shared_client = foursquare.Foursquare(client_id=FOURSQUARE_CLIENT_ID, client_secret=FOURSQUARE_CLIENT_SECRET)



