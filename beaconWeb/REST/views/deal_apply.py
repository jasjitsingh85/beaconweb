from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import authentication
from beaconWeb.apps.beacon.common.utils.deals import apply_for_deal, get_image_url
from beaconWeb.REST.serializers import BeaconWithDealStatusSerializer
from rest_framework.authtoken.models import Token
from rest_framework import status
from datetime import datetime
from beaconWeb.apps.beacon.common.common_utils import add_extra_hotspot_properties


class DealApplyAPI(APIView):

    """
    Set a new deal
    POST - Required Params:
    deal_id -- ID of deal
    time -- UNIX time stamp for deal start time
    custom_message -- message associated with deal
    invite_list[] --  invite_list[] usage: &invite_list[]={name:kamran, phone:123}&invite_list[]=...)
    """

    authentication_classes = (authentication.TokenAuthentication,)

    def post(self, request, format=None):
        response = {}
        user = Token.objects.get(key=request.auth).user
        invite_list = request.DATA.getlist('invite_list[]')
        deal_id = request.DATA['deal_id']
        timestamp = float(request.DATA['time'])
        image_url = get_image_url(request.DATA)
        print "Timestamp: " + str(timestamp)
        custom_message = request.DATA.get('custom_message')
        deal, beacon = apply_for_deal(user, deal_id, timestamp, invite_list, custom_message, image_url)
        beacon = add_extra_hotspot_properties(beacon)
        beacon.deal = deal
        serializer = BeaconWithDealStatusSerializer(beacon)
        response['beacon'] = serializer.data
        return Response(response, status=status.HTTP_200_OK)