from django.conf import settings
from django.shortcuts import render_to_response
from django.template import RequestContext
from beaconWeb.apps.happy_hours.form import SelectForm
from beaconWeb.apps.beacon.common.utils.encryption import simple_int_hash
from beaconWeb.apps.beacon.models import *
from beaconWeb.apps.happy_hours.models import City, Neighborhood, HappyHour
from django.http import HttpResponseRedirect
from beaconWeb.apps.happy_hours.utils import get_days, get_times, get_happy_hours, get_neighborhoods, get_today_day, get_time, get_yelp_info, get_day_and_time
from beaconWeb.apps.happy_hours.web_utils import get_title, get_client_ip
from django.views.decorators.clickjacking import xframe_options_exempt

@xframe_options_exempt
def index(request, city=None, day=None, time=None, neighborhood=None, page=1):
    context_dict = {}
    ip_address = get_client_ip(request)
    print ip_address
    if day is None:
        day = get_today_day()
    if (city != "None") and (city is not None):
        city = city.replace('47', '/')
    if City.objects.filter(name=city).count() == 1:
        city = City.objects.get(name=city)
    else:
        # city = get_city_from_ip(ip_address)
        city = City.objects.get(pk=68)
    if time is None:
        time = get_time()
    form = SelectForm()
    if (neighborhood != "None") and (neighborhood is not None):
        neighborhood = neighborhood.replace("27", "'").replace("45","-")
        neighborhood_obj = Neighborhood.objects.get(city=city, name=neighborhood)
        form.fields['neighborhood'].initial = neighborhood_obj.id
    form.fields['city'].initial = city.id
    form.fields['day'].initial = day
    form.fields['time'].initial = time
    form.fields['neighborhood'].choices = get_neighborhoods(city.name)
    context_dict['ip'] = ip_address
    context_dict['request'] = request
    context_dict['cities'] = City.objects.all()
    context_dict['days'] = get_days()
    context_dict['times'] = get_times()
    context_dict['current'] = [city.name, day, time, neighborhood, page]
    context_dict['happy_hours'], context_dict['pages'], context_dict['total_happy_hours'] = get_happy_hours(city.name, day, neighborhood, time, page)
    context_dict['title'] = get_title(context_dict['total_happy_hours'], neighborhood, city, day, time)
    context_dict['form'] = form
    return render_to_response('beaconWeb/apps/happy_hours/templates/index.html', context_dict, context_instance=RequestContext(request))


# def update(request):
#     context_dict = {}
#     form = SelectForm()
#     city_id = request.POST['city']
#     city = City.objects.get(id=city_id)
#     day = request.POST['day']
#     time = request.POST['time']
#     neighborhood_id = request.POST['neighborhood']
#     if neighborhood_id != "0":
#         neighborhood = Neighborhood.objects.get(id=neighborhood_id)
#         neighborhood_name = neighborhood.name.replace("'","27")
#     else:
#         neighborhood_name = "None"
#     page = "1"
#     url = "/happy-hours/" + city.name + "/" + neighborhood_name + "/" + day + "/" + time + "/" + page
#     return HttpResponseRedirect(url)

@xframe_options_exempt
def detail(request, happy_hour_id, place_name):
    context_dict = {}
    happy_hour = HappyHour.objects.get(pk=happy_hour_id)
    context_dict['yelp_ratings'], context_dict['yelp_url'] = get_yelp_info(happy_hour)
    context_dict['title'] = happy_hour.place.name
    context_dict['image'] = happy_hour.place.large_image_url
    context_dict['description'] = happy_hour.description
    context_dict['latitude'] = happy_hour.place.latitude
    context_dict['longitude'] = happy_hour.place.longitude
    context_dict['address'] = happy_hour.place.street_address
    context_dict['phone'] = happy_hour.place.phone
    context_dict['foursquare_id'] = happy_hour.place.foursquare_id
    context_dict['yelp_id'] = happy_hour.place.yelp_id
    context_dict['day_and_time'] = get_day_and_time(happy_hour)
    return render_to_response('beaconWeb/apps/happy_hours/templates/detail.html', context_dict, context_instance=RequestContext(request))

