from django.db import models
import time
from datetime import timedelta
from beaconWeb.settings import YELP_CONSUMER_KEY, YELP_TOKEN, YELP_CONSUMER_SECRET, YELP_TOKEN_SECRET
from beaconWeb.apps.beacon.classes.foursquare_client import FoursquareClient
from yelpapi import YelpAPI
from bitfield import BitField
from beaconWeb.common_utils import prettify_phone_number
from beaconWeb.common_utils import smart_format, smart_str


class City(models.Model):
    gt_id = models.IntegerField(unique=True, db_index=True)
    name = models.CharField(max_length=128)
    state_name = models.CharField(max_length=128)

    @classmethod
    def create_with_json(cls, json):
        city_id = json['@id']
        city, created = City.objects.get_or_create(gt_id=city_id)
        name = json['@name']
        city.name = name
        city.save()
        return city

    def __unicode__(self):
        return unicode(self.name)


class Neighborhood(models.Model):
    name = models.CharField(max_length=128)
    city = models.ForeignKey(City, related_name='neighborhoods')


class Place(models.Model):
    gt_id = models.IntegerField(unique=True, db_index=True, blank=True, null=True)
    name = models.CharField(max_length=128)
    street_address = models.CharField(max_length=128)
    zip_code = models.CharField(max_length=10)
    phone = models.CharField(max_length=20, blank=True, null=True)
    longitude = models.FloatField(db_index=True)
    latitude = models.FloatField(db_index=True)
    image_url = models.CharField(max_length=256, blank=True, null=True)
    yelp_id = models.CharField(max_length=128, blank=True, null=True)
    yelp_rating_image_url = models.CharField(max_length=256, blank=True, null=True)
    yelp_review_count = models.IntegerField(blank=True, null=True)
    foursquare_id = models.CharField(max_length=128, blank=True, null=True)
    facebook_id = models.CharField(max_length=128, blank=True, null=True)
    city = models.ForeignKey(City, related_name='places', blank=True, null=True)
    neighborhood = models.ForeignKey(Neighborhood, blank=True, null=True, related_name='places')
    date_updated = models.DateTimeField("Date Updated", auto_now=True)
    place_description = models.TextField()

    class Meta:
        app_label = 'happy_hours'

    def __unicode__(self):
        if self.city:
            return unicode(self.name)+' ' + self.city.__unicode__()
        return unicode(self.name)

    @property
    def large_image_url(self):
        image_url = None
        if self.image_url:
            image_url = self.image_url.replace('ms.jpg', 'o.jpg')
        return image_url

    def load_extras(self):
        self.rating = None
        self.review_count = None
        self.photos = None
        self.price = None
        if self.yelp_id:
            self.yelp_extras()
        if self.foursquare_id:
            self.foursquare_extras()

    def yelp_extras(self):
        yelp_api = YelpAPI(YELP_CONSUMER_KEY, YELP_CONSUMER_SECRET, YELP_TOKEN, YELP_TOKEN_SECRET)
        result = yelp_api.business_query(id=self.yelp_id)
        img_key = 'rating_img_url_large'
        if img_key in result:
            self.rating_image_url = result[img_key]
        phone_key = 'phone'
        if phone_key in result:
            self.phone = prettify_phone_number(result[phone_key])

        rating_key = 'rating'
        if rating_key in result:
                self.rating = result[rating_key]
        review_count_key = 'review_count'
        if review_count_key in result:
            self.review_count = result[review_count_key]
        location_key = 'location'
        if location_key in result:
            location_data = result[location_key]
            self.zip_code = location_data['postal_code']
            self.street_address = location_data['address'][0]
            self.save()

    def foursquare_extras(self):
        result = FoursquareClient.shared_client.venues(self.foursquare_id)
        venue = result['venue']
        if 'price' in venue and 'tier'in venue['price']:
            price = venue['price']['tier']
            self.price = price
        if 'photos' in venue and venue['photos']['count']:
            print venue['photos']
            photos_data = venue['photos']['groups'][0]['items']
            photo_urls = []
            #print photos_data
            for photo in photos_data:
                suffix = photo['suffix']
                prefix = photo['prefix']
                url = "{0}{1}{2}".format(prefix, 'original', suffix)
                photo_urls.append(url)
            self.photos = photo_urls
        return result


    @classmethod
    def create_with_json(cls, json, city=None):
        place_id = json['id']
        filtered = Place.objects.filter(gt_id=place_id)
        if filtered.exists():
            place = filtered[0]
        else:
            place = Place(gt_id=place_id)
        latitude = json['address']['lat']
        if latitude is None:
            latitude = 0
        longitude = json['address']['long']
        if longitude is None:
            longitude = 0
        zip_code = json['address']['zip']
        street = json['address']['street']
        place.latitude = latitude
        place.longitude = longitude
        place.zip = zip_code
        place.street_address = street
        place.name = json['name']
        place.city = city
        place.save()

        if 'happy_hour' in json['happy_hours']:
            happy_hour_json = json['happy_hours']['happy_hour']
            HappyHour.create_with_json(happy_hour_json, place=place)

        return place


class HappyHour(models.Model):
    gt_id = models.IntegerField(unique=True, db_index=True, null=True, blank=True, default=None)
    description = models.TextField()
    start = models.FloatField(blank=True, null=True, default=None)
    end = models.FloatField(blank=True, null=True, default=None)
    days = models.CharField(max_length=7)
    place = models.ForeignKey(Place, related_name='happy_hours')
    days_active = BitField(flags=('Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'), blank=True, null=True)
    date_updated = models.DateTimeField("Date Updated", auto_now=True)

    class Meta:
        app_label = 'happy_hours'

    def save(self, *args, **kwargs):
        days = HappyHour.days_active
        day_bits = [days.Sunday, days.Monday, days.Tuesday, days.Wednesday, days.Thursday, days.Friday, days.Saturday, days.Sunday]
        bitfield = 0
        for i in range(0, 7):
            if self.days[i] == "1":
                bitfield = bitfield | day_bits[i]
        self.days_active = bitfield
        super(HappyHour, self).save(*args, **kwargs)

    def __unicode__(self):
        return smart_format("{0}:{1}", self.place, self.description)


    @classmethod
    def create_with_json(cls, json, place=None):
        happy_hour_id = json['id']
        filtered = HappyHour.objects.filter(gt_id=happy_hour_id)
        if filtered.exists():
            happy_hour = filtered[0]
        else:
            happy_hour = HappyHour(gt_id=happy_hour_id)
        happy_hour.description = json['description']
        try:
            start_time = time.strptime(json['start_time'], '%I:%M %p')
            happy_hour.start = timedelta(hours=start_time.tm_hour, minutes=start_time.tm_min).total_seconds()
        except:
            print "happy hour doesn't have start time"
        try:
            end_time = time.strptime(json['end_time'], '%I:%M %p')
            happy_hour.end = timedelta(hours=end_time.tm_hour, minutes=end_time.tm_min).total_seconds()
        except:
            print "happy hour doesn't have end time"
        happy_hour.days = json['days']
        happy_hour.place = place
        happy_hour.save()
        return happy_hour





