from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import authentication
from beaconWeb.apps.beacon.common.utils.deals import check_in_for_venue, is_deal_active
from beaconWeb.REST.serializers import BeaconWithDealStatusSerializer, TabItemSerializer, TabSerializer
from rest_framework.authtoken.models import Token
from rest_framework import status
from datetime import datetime
from beaconWeb.apps.beacon.common.common_utils import add_extra_hotspot_properties


class CheckInV2API(APIView):

    """
    """

    authentication_classes = (authentication.TokenAuthentication,)

    def post(self, request, format=None):
        response = {}
        user = Token.objects.get(key=request.auth).user
        print str(request.DATA)
        deal, beacon, tab, tab_items = check_in_for_venue(user, request.DATA)
        beacon = add_extra_hotspot_properties(beacon)
        beacon.deal = deal
        serializer = BeaconWithDealStatusSerializer(beacon)
        response['beacon'] = serializer.data
        if tab:
            response['tab_items'] = TabItemSerializer(tab_items, many=True).data
            response['tab'] = TabSerializer(tab).data
        return Response(response, status=status.HTTP_200_OK)

    def get(self, request, format=None):
        response = {}
        user = Token.objects.get(key=request.auth).user
        response['active'] = is_deal_active(user, request.QUERY_PARAMS)
        return Response(response, status=status.HTTP_200_OK)
