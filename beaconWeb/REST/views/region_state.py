from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import authentication
from beaconWeb.apps.beacon.models.deal import Deal
from beaconWeb.apps.beacon.models.region_state import RegionState
from beaconWeb.apps.beacon.common.utils.deals import deal_hours_for_datetime
from rest_framework.authtoken.models import Token
from beaconWeb.REST.serializers import DealSerializer
from rest_framework import status
from datetime import datetime, timedelta


class RegionStateAPI(APIView):

    """
    When a user walks in range of a beacon
    POST - Required params: deal_id, region_state, region_type
    region_state -- region state (see GDoc for iBeacon implementation)
    region_type -- region type (see GDoc for iBeacon implementation)
    """

    authentication_classes = (authentication.TokenAuthentication,)

    def post(self, request, format=None):
        response = {}
        data = request.DATA
        auth_token = request.auth
        token = Token.objects.get(key=auth_token)
        deal_id = int(data['deal_id'])
        region_state = data['region_state']
        region_type = data['region_type']
        print "Deal ID for Region State: " + str(deal_id)
        if Deal.objects.filter(pk=deal_id).exists():
            deal = Deal.objects.get(pk=deal_id)
            show_notification = deal.active
            #get region states in last day
            past_states = RegionState.objects.filter(user=token.user, place=deal.place, showed_notification=True,
                                                     date_created__gte=datetime.now()-timedelta(hours=12))
            if past_states.exists():
                show_notification = False

            deal_hours = deal_hours_for_datetime(deal, datetime.now())
            if not deal_hours:
                show_notification = False

            region_state =  RegionState.objects.create(user=token.user, place=deal.place, region_state=region_state,
                                                       region_type=region_type, showed_notification=show_notification)
            response['deals'] = DealSerializer(deal).data
            response['show_notification'] = show_notification
        return Response(response, status=status.HTTP_200_OK)