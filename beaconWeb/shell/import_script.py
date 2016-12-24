# from beaconWeb.apps.beacon.common.utils.rewards import *
from django.contrib.auth.models import User
# from datetime import datetime, timedelta
from beaconWeb.apps.beacon.common.utils.payments import *
from beaconWeb.apps.beacon.retention.emails import *
from beaconWeb.apps.beacon.retention.push import *
# from beaconWeb.apps.beacon.data.temp import *
from beaconWeb.apps.beacon.common.common_utils import *
from beaconWeb.apps.beacon.common.chron import *
from beaconWeb.apps.beacon.tasks.send_sms import *
from beaconWeb.apps.beacon.common.utils.rewards import *
from beaconWeb.apps.beacon.common.utils.events import *
from beaconWeb.apps.beacon.data.happy_hour_scraper import *
from beaconWeb.apps.beacon.data.instagram_scraper import *
from beaconWeb.apps.beacon.data.common_scraper_utils import *
from beaconWeb.apps.beacon.data.facebook_scraper import *
from beaconWeb.apps.beacon.data.place_scraper import *
from beaconWeb.apps.beacon.data.yelp_scraper import *
from beaconWeb.apps.beacon.data.foursquare_scraper import *
from beaconWeb.apps.beacon.data.place_type_scraper import *
from beaconWeb.apps.beacon.data.website_scraper import *
from beaconWeb.apps.beacon.common.utils.friends import *
from beaconWeb.apps.beacon.analytics.updated_analytics import *
from beaconWeb.apps.beacon.common.utils.point_of_sale import *
from beaconWeb.apps.beacon.common.utils.tracker import *
from beaconWeb.apps.beacon.common.utils.sponsored_events import *
from beaconWeb.apps.beacon.common.utils.event_staffer import *
from beaconWeb.apps.beacon.common.utils.email_campaign import *
from beaconWeb.apps.beacon.common.utils.push_campaign import *
from beaconWeb.facebook_ads_api import HotspotFacebookAds

activated_users = User.objects.filter(profile__activated=True)
user_count = activated_users.count()
user_count_today = activated_users.filter(date_joined__gte=datetime.now()-timedelta(days=1)).count()
#deal_places = DealPlace.objects.filter(latitude__range=lat_range, longitude__range=lng_range)

print "User Count\nTotal: {0}\nToday: {1}".format(user_count, user_count_today)

try:
    jeff = User.objects.get(username='6176337532')
    print "stored user {0} in variable jeff".format(jeff)
except:
    print "could not get user jeff"

try:
    jas = User.objects.get(username='5413359388')
    print "stored user {0} in variable jas".format(jas)
except:
    print "could not get user jas"

try:
    will = User.objects.get(username='6094398069')
    print "stored user {0} in variable will".format(will)
except:
    print "could not get user will"

try:
    jared = User.objects.get(username='2162695105')
    print "stored user {0} in variable jared".format(jared)
except:
    print "could not get user jared"

try:
    ryan = User.objects.get(username='2064731300')
    print "stored user {0} in variable ryan".format(ryan)
except:
    print "could not get user ryan"

try:
    samm = User.objects.get(username='2625104546')
    print "stored user {0} in variable samm".format(samm)
except:
    print "could not get user samm"

