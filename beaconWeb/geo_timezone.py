import time
import requests
import pytz


class GeoTimeZone(object):
    BASE_URL = 'https://maps.googleapis.com/maps/api/timezone/json'

    def get_timezone(self, latitude, longitude, timestamp=time.time(), sensor=False):
        params_string = "?"
        params_string += "location={0},{1}".format(latitude, longitude)
        params_string += "&timestamp={0}".format(timestamp)
        if sensor:
            sensor_string = "true"
        else:
            sensor_string = "false"
        params_string += "&sensor={0}".format(sensor_string)
        params_string += "&key={0}".format("AIzaSyBZv2lCx8W-e59CgnFT_cYjKqX_uoJutlU")
        absolute_url = "".join([GeoTimeZone.BASE_URL, params_string])
        response = requests.get(absolute_url)
        print response.json()
        timezone = pytz.timezone(response.json()['timeZoneId'])
        return timezone

    def get_timezone_id(self, latitude, longitude, timestamp=time.time(), sensor=False):
        params_string = "?"
        params_string += "location={0},{1}".format(latitude, longitude)
        params_string += "&timestamp={0}".format(timestamp)
        if sensor:
            sensor_string = "true"
        else:
            sensor_string = "false"
        params_string += "&sensor={0}".format(sensor_string)
        params_string += "&key={0}".format("AIzaSyBZv2lCx8W-e59CgnFT_cYjKqX_uoJutlU")
        absolute_url = "".join([GeoTimeZone.BASE_URL, params_string])
        response = requests.get(absolute_url)
        print response.json()
        return response.json()['timeZoneId']

    def get_python_timezone(self, timezone_id):
        return pytz.timezone(timezone_id)
