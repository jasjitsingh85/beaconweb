from models import HappyHour, City, District, Place
import xmltodict
import requests
import pickle
import os
import sys
import logging

def parse_request(request):
    data = xmltodict.parse(request.text)
    cities_data = data['resultSet']['cities']['city']
    for city_data in cities_data:
        City.create_with_json(city_data)

    current_city_id = data['resultSet']['current_city']
    current_city = City.objects.get(gt_id=current_city_id)
    if 'place' not in data['resultSet']['places']:
        return
    places_data = data['resultSet']['places']['place']
    if isinstance(places_data, list):
        for place_data in places_data:
            Place.create_with_json(place_data, city=current_city)
    else:
        Place.create_with_json(places_data, city=current_city)


def parse_all_requests_at_path(path, ext='.txt'):
    my_logger = logging.getLogger("logfun")
    my_logger.setLevel(logging.DEBUG)
    h = logging.StreamHandler()
    f = logging.Formatter("%(levelname)s %(asctime)s %(funcName)s %(lineno)d %(message)s")
    h.setFormatter(f)
    my_logger.addHandler(h)
    files_names = []
    for f in os.listdir(path):
        if f.endswith(ext):
            files_names.append(path+'/'+f)
    for file_name in files_names:
        hr_requests = pickle.load(open(file_name))
        for r in hr_requests:
            try:
                parse_request(r)
            except:
                my_logger.exception("error")
                return r
        print 'finished {0}'.format(file_name)