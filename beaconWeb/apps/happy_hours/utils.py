from models import HappyHour, Place, City, Neighborhood
from beaconWeb.common_utils import distance_between_two_points
from models import HappyHour, Place
from beaconWeb.common_utils import distance_between_two_points
from django.db.models import Q
from bitfield import BitField
from datetime import timedelta, datetime


def fetch_happy_hours(latitude, longitude, day, time, now=True, upcoming=True):
    lat_range = [latitude-0.1, latitude+0.1]
    lon_range = [longitude-0.1, longitude+0.1]
    bitmask = bitmask_for_day(day)
    happy_hours = HappyHour.objects.filter(days_active=bitmask, place__latitude__range=lat_range, place__longitude__range=lon_range).exclude(place__yelp_id=None).select_related('place')
    if now and upcoming:
        happy_hours = happy_hours.filter(end__gte=time)
    elif now:
        happy_hours = happy_hours.filter(start__lte=time, end__gte=time)
    elif upcoming:
        happy_hours = happy_hours.filter(start__gte=time)

    for happy_hour in happy_hours:
        happy_hour.is_followed = False
        happy_hour.place.distance = distance_between_two_points(latitude, longitude,
                                                                happy_hour.place.latitude, happy_hour.place.longitude)
    happy_hours = list(happy_hours)
    happy_hours.sort(key=lambda x: x.place.distance)

    return happy_hours


def bitmask_for_day(day):
    days = [HappyHour.days_active.Sunday,
            HappyHour.days_active.Monday,
            HappyHour.days_active.Tuesday,
            HappyHour.days_active.Wednesday,
            HappyHour.days_active.Thursday,
            HappyHour.days_active.Friday,
            HappyHour.days_active.Saturday]
    return days[day - 1]


def get_days():
    return ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]


def get_times():
    return ["Afternoon", "Evening", "Night"]


def convert_day_string_to_int(day):
    days = get_days()
    index = days.index(day)
    return index


def get_begin_and_end_time(time):
    if time == "Afternoon":
        return 43200, 57600
    elif time == "Evening":
        return 57600, 72000
    elif time == "Night":
        return 72000, 86400
    elif time == "Any":
        return 0, 86400


def get_neighborhood(city, neighborhood):
    if Neighborhood.objects.filter(city_id=city.id, name=neighborhood).count() == 1:
        return Neighborhood.objects.get(city_id=city.id, name=neighborhood)
    else:
        return None


def get_happy_hours(city="Omaha", day="Monday", neighborhood=None, time="Afternoon", pages=1):
    day_as_int = convert_day_string_to_int(day)
    bitmask = bitmask_for_day(day_as_int)
    city = City.objects.get(name=city)
    neighborhood = get_neighborhood(city, neighborhood)
    if neighborhood:
        places = Place.objects.filter(city=city, neighborhood=neighborhood)
    else:
        places = Place.objects.filter(city=city)
    # places = Place.objects.filter(city=city)
    begin_time, end_time = get_begin_and_end_time(time)
    happy_hours = HappyHour.objects.filter(Q(start__range=(begin_time, end_time))|Q(end__range=(begin_time,end_time)))
    all_happy_hours = happy_hours.filter(days_active=bitmask, place__in=places).exclude(place__yelp_id=None)
    happy_hours_on_page = get_happy_hours_for_page(all_happy_hours, pages)
    total_happy_hours = len(all_happy_hours)
    pages_number = abs(len(all_happy_hours)/20) + 1
    pages = get_page_array(pages_number)
    return happy_hours_on_page, pages, total_happy_hours


def get_neighborhoods(city):
    if City.objects.filter(name=city).exists():
        city_obj = City.objects.get(name=city)
        neighborhoods = [(c.id, c.name) for c in Neighborhood.objects.filter(city=city_obj).order_by('name')]
        neighborhoods.insert(0, (0, u'Select'))
        return neighborhoods


def get_page_array(pages):
    page_array = []
    for x in range(0, pages):
        page_array.append(x + 1)
    return page_array


def get_happy_hours_for_page(happy_hours, pages=1):
    print happy_hours
    print pages
    number_per_page = 20
    begin_at_index = ((int(pages)-1) * number_per_page)
    end_at_index = begin_at_index + (number_per_page)
    return happy_hours[begin_at_index:end_at_index]


def get_today_day():
    now = datetime.now()
    return now.strftime("%A")


def get_time():
    now = datetime.now()
    current_hour = now.hour
    print current_hour
    if now.hour < 16:
        return "Afternoon"
    elif current_hour >= 16 and current_hour < 20:
        return "Evening"
    elif current_hour >= 20 and current_hour <= 24:
        return "Night"


def get_yelp_info(happy_hour):
    place = happy_hour.place
    place.yelp_extras()
    print place.review_count
    print place.rating_image_url
    return place.review_count, place.rating_image_url


def get_day_and_time(happy_hour):
    times = get_times_to_string(happy_hour.start,happy_hour.end)
    days = get_days_as_string(happy_hour.days)
    return days + ": " + times


def get_days_as_string(days):
    bit = BitField(flags=('Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'))
    list_of_days = []
    days = str(days)
    for i in range(0,7):
        if days[i]=="1":
            list_of_days.append(bit.flags[i])
    return ', '.join(list_of_days)


def get_times_to_string(start, end):
    start = convert_time(start)
    end = convert_time(end)
    return start + "-" + end


def convert_time(time):
    sec = timedelta(seconds=int(time))
    d = datetime(1,1,1) + sec
    AM_or_PM = get_am_or_pm(d.hour)
    return str(d.hour%12) + ":" + str('%02d' % d.minute) + AM_or_PM


def get_am_or_pm(hour):
    if hour < 12:
        return "am"
    else:
        return "pm"