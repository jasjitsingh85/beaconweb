from django.conf.urls import patterns, include, url
from django.contrib import admin
from beaconWeb.apps.beacon.views import *
from beaconWeb.apps.merchant.views import *
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
admin.autodiscover()

urlpatterns = patterns('',
    url(r'^admin/', include(admin.site.urls)),
    # url(r'^happy-hours/', include('beaconWeb.apps.happy_hours.urls')),
    url(r'^/?$', dashboard, name="dashboard"),
    url(r'^api/', include('beaconWeb.REST.urls')),
    # url(r'^hotspot/(?P<beacon_follow_id>\w+)/$', hotspot_mobile, name="hotspot_mobile"),
    url(r'^hotspot-deal/(?P<deal_status_id>\w+)/$', hotspot_deal, name="hotspot_deal"),
    url(r'^dashboard/$', dashboard, name="dashboard"),
    url(r'^officehero/$', free_drink_coupon, name="free-drink-coupon"),
    url(r'^privacy/$', privacy, name="privacy"),
    url(r'^support/$', support, name="support"),
    url(r'^terms/$', terms, name="terms"),
    url(r'^promo/$', merchant, name="merchant"),
    url(r'^ios-notifications/', include('ios_notifications.urls')),
    url(r'^api-docs/', include('rest_framework_swagger.urls')),
    url(r'^feedback/(?P<user_id>\w+)/(?P<event_id>\w+)/(?P<nps_score>\w+)/$', save_feedback),
    url(r'^feedback/(?P<feedback_id>\w+)/submit/$', submit_comments, name="submit"),
    url(r'^payment/(?P<event_id>\w+)/$', load_payment, name="load_payment"),
    url(r'^checkout/$', checkout, name="checkout"),
    url(r'^manager/(?P<event_staffer_id>\w+)/$', load_event_staffer, name="load_event_staffer"),
    url(r'^subscribe/(?P<market_name>[\w|\W]+)/$', load_email_capture, name="load_email_capture"),
    url(r'^email-response/(?P<email>[\w|\W]+)/(?P<event_id>[\w|\W]+)/(?P<response_boolean>[\w|\W]+)/$', load_email_response, name="load_email_response"),
    url(r'^unsubscribe/(?P<email>[\w|\W]+)/(?P<event_id>[\w|\W]+)/$', load_unsubscribe_form, name="load_unsubscribe_form"),
    url(r'^tickets/(?P<ticket_id>[\w|\W]+)/$', load_ticket_page, name="load_ticket_page"),
    url(r'^promo/(?P<ticket_id>[\w|\W]+)/$', load_promo_ticket_page, name="load_promo_ticket_page"),
    url(r'^early-access/(?P<ticket_id>[\w|\W]+)/$', load_early_access_page, name="load_early_access_page"),
    url(r'^subscription/(?P<ticket_id>[\w|\W]+)/$', load_email_capture_for_event, name="load_email capture for event"),
    url(r'^facebook-share/(?P<event_id_hash>[\w|\W]+)/$', load_facebook_share, name="load_facebook_share"),
)

urlpatterns += staticfiles_urlpatterns()

urlpatterns += patterns('',
    (r'^django-rq/', include('django_rq.urls')),
)