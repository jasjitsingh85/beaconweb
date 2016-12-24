import time
import requests
from pytz import timezone
import pytz
from datetime import datetime, timedelta
from beaconWeb.geo_timezone import GeoTimeZone


class DateFormatter(object):

    def __init__(self, tz=timezone('US/Eastern'), time_format='%I:%M%p'):
        self.tz = tz
        self.time_format = time_format

    def string_for_timestamp(self, timestamp=time.time()):
        loc_dt = datetime.fromtimestamp(timestamp, tz=self.tz)
        time_string = loc_dt.strftime(self.time_format)
        #remove any leading zeros
        time_string = time_string.strip('0')
        return time_string


    def friendly_string_for_datetime(self, dt=datetime.now(tz=timezone('US/Eastern'))):
        if self.isToday(dt):
            time_format = '%I:%M%p'
            date_string = "Today, {0}".format(dt.strftime(time_format).strip('0'))
        elif self.isTomorrow(dt):
            time_format = '%I:%M%p'
            date_string = "Tomorrow, {0}".format(dt.strftime(time_format).strip('0'))
        else:
            day_string = dt.strftime('%A, %B %d')
            time_string = dt.strftime('%I:%M%p').strip('0')
            date_string = "{0} {1}".format(day_string, time_string)
        return date_string

    def friendly_string_for_timestamp(self, timestamp, latitude, longitude):
        try:
            self.tz = GeoTimeZone().get_timezone(latitude, longitude, timestamp)
        except:
            print 'something went wrong'
        loc_dt = datetime.fromtimestamp(timestamp, tz=self.tz)
        return self.friendly_string_for_datetime(loc_dt)


    def isToday(self, dt=datetime.now(tz=timezone('US/Eastern'))):
        now = datetime.now(tz=self.tz).date()
        return now == dt.date()


    def isTomorrow(self, dt=datetime.now(tz=timezone('US/Eastern'))):
        tomorrow = datetime.now(tz=self.tz).date() + timedelta(days=1)
        return tomorrow == dt.date()

