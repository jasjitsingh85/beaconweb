from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import authentication
from beaconWeb.apps.beacon.common.utils.deals import check_in_for_deal, check_in_for_happy_hour, is_deal_active
from beaconWeb.REST.serializers import BeaconWithDealStatusSerializer
from rest_framework.authtoken.models import Token
from rest_framework import status
from datetime import datetime
from beaconWeb.apps.beacon.common.common_utils import add_extra_hotspot_properties


class CheckInAPI(APIView):

    """
    """

    authentication_classes = (authentication.TokenAuthentication,)

    def post(self, request, format=None):
        response = {}
        user = Token.objects.get(key=request.auth).user
        isDeal = bool(int(request.DATA['is_deal']))
        if isDeal:
            deal, beacon = check_in_for_deal(user, request.DATA)
            beacon = add_extra_hotspot_properties(beacon)
            beacon.deal = deal
            serializer = BeaconWithDealStatusSerializer(beacon)
            response['beacon'] = serializer.data
        else:
            response['beacon'] = check_in_for_happy_hour(user, request.DATA)
        return Response(response, status=status.HTTP_200_OK)

    def get(self, request, format=None):
        response = {}
        user = Token.objects.get(key=request.auth).user
        response['active'] = is_deal_active(user, request.QUERY_PARAMS)
        return Response(response, status=status.HTTP_200_OK)
