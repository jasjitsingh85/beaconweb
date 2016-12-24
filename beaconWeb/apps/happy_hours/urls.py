from django.conf.urls import patterns, url
from beaconWeb.apps.happy_hours.views import index, detail


urlpatterns = patterns('REST.views',
        url(r'^/?$', index, name="index"),
        # url(r'^/?update/$', update, name="update"),
        url(r'^/?places/(?P<happy_hour_id>[\w ]+)/(?P<place_name>[\w ]+)$', detail, name="detail"),
        url(r'^/?(?P<city>[\w ]+)/(?P<neighborhood>[\w ]+)/(?P<day>[\w ]+)/(?P<time>[\w ]+)/(?P<page>[\w ]+)$', index, name="index"),
)

