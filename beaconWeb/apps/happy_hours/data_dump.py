from beaconWeb.settings import RQ_THREAD
from django_rq import job
from models import City, Place, Neighborhood, HappyHour
from beaconWeb.common_utils import smart_str
import csv

null_string = "NULL"
city_attributes = ['gt_id', 'name', 'state_name']
places_attributes = ['gt_id', 'zip_code', 'longitude', 'latitude', 'name', 'city.gt_id', 'street_address', 'image_url', 'yelp_id', 'phone', 'foursquare_id', 'neighborhood_id']
neighborhood_attributes = ['name', 'city.gt_id']
happy_hour_attributes = ['description', 'end', 'days', 'gt_id', 'start', 'days_active', 'place.gt_id']


def dump_cities():
    cities = City.objects.all().order_by('pk')
    create_csv(city_attributes, cities, 'cities.csv')


def dump_places():
    places = Place.objects.all().order_by('pk')
    create_csv(places_attributes, places, 'places.csv')


def dump_neighborhoods():
    neighborhoods = Neighborhood.objects.all().order_by('pk')
    create_csv(neighborhood_attributes, neighborhoods, 'neighborhoods.csv')

def dump_happy_hours():
    happy_hours = HappyHour.objects.all().order_by('pk').select_related('place')
    create_csv(neighborhood_attributes, happy_hours, 'happy_hours.csv')



def dump_field(field_name, objects):
    dump = []
    for obj in objects:
        value = smart_str(deepgetattr(obj, field_name))
        if not value:
            value = null_string
        else:
            value = value.replace(';', ',')
        dump.append(value)
    return dump


def deepgetattr(obj, attr):
    """Recurses through an attribute chain to get the ultimate value."""
    return reduce(getattr, attr.split('.'), obj)


def create_csv(attribute_names, objects, filename="test.csv",):
    args = []
    for name in attribute_names:
        args.append(dump_field(name, objects))
    data = []
    for i in range(len(args)):
        data.append([attribute_names[i]] + args[i])

    data = zip(*data)
    with open(filename, 'w') as fp:
        a = csv.writer(fp, delimiter=',')
        a.writerows(data)


@job(RQ_THREAD)
def process_csv(csvfile):
    processors = {'cities.csv': city_row_processor,
                  'neighborhoods.csv': neighborhood_row_processor,
                  'places.csv': place_row_processor,
                  'happy_hours.csv': happy_hour_row_processor}
    row_processor = processors[str(csvfile)]
    reader = csv.reader(csvfile)
    first_row = True
    for row in reader:
        if first_row:
            first_row = False
        elif len(row) > 1:
            row_processor(row)


def city_row_processor(row):
    gt_id = row[0]
    name = row[1]
    state_name = row[2]
    city, created = City.objects.get_or_create(gt_id=gt_id, name=name, state_name=state_name)


def neighborhood_row_processor(row):
    neighborhood_attributes = ['name', 'city.gt_id']
    #name = row[0]
    #city_gt_id = row[1]
    #print name
    #print City.objects.get(gt_id=city_gt_id).name


def place_row_processor(row):
    gt_id = row[0]
    zip_code = row[1]
    longitude = row[2]
    latitude = row[3]
    name = row[4]
    city_gt_id = row[5]
    street_address = row[6]
    image_url = row[7]
    yelp_id = row[8]
    phone = row[9]
    foursquare_id = row[10]
    neighborhood_id = row[11]
    city = City.objects.get(gt_id=city_gt_id)
    place, created = Place.objects.get_or_create(gt_id=gt_id, zip_code=zip_code, longitude=longitude, latitude=latitude,
                                                 name=name, street_address=street_address, image_url=image_url,
                                                 yelp_id=yelp_id, phone=phone, foursquare_id=foursquare_id, city=city)
    print smart_str(place.name)


def happy_hour_row_processor(row):
    description = row[0]
    end = row[1]
    if not end or end == 'None':
        end = 0
    days = row[2]
    gt_id = row[3]
    start = row[4]
    days_active = row[5]
    place_gt_id = row[6]
    place = Place.objects.get(gt_id=place_gt_id)
    happy_hour, created = HappyHour.objects.get_or_create(description=description, end=end, days=days,
                                                          gt_id=gt_id, start=start, days_active=days_active, place=place)
    print smart_str(happy_hour.description)



def clean_up_import():
    no_yelp = Place.objects.filter(yelp_id='None')
    for place in no_yelp:
        place.yelp_id = None
        place.save()
    no_foursquare = Place.objects.filter(foursquare_id='None')
    for place in no_foursquare:
        place.foursquare_id = None
        place.save()