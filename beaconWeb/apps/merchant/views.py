from django.conf import settings
from django.shortcuts import render_to_response
from django.template import RequestContext
from beaconWeb.apps.beacon.common.utils.encryption import simple_int_hash
from beaconWeb.apps.beacon.models import *
from django.shortcuts import render
from django.http import HttpResponseRedirect
from beaconWeb.apps.beacon.forms import UploadFileForm
from beaconWeb.apps.beacon.analytics.analytics import *
from beaconWeb.apps.happy_hours.data_dump import process_csv
from beaconWeb.apps.beacon.common.utils.deals import get_deal_status
from beaconWeb.REST.serializers import DealStatusSerializer, BeaconWithDealStatusSerializer
import csv


def merchant(request):
    context_dict = {}
    return render_to_response('beaconWeb/apps/beacon/templates/promo.html', context_dict, context_instance=RequestContext(request))# Create your views here.
