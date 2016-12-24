from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import authentication
from beaconWeb.apps.beacon.models.deal import Deal
from beaconWeb.apps.beacon.common.utils.rewards import get_active_vouchers, get_nearby_rewards, add_points
from beaconWeb.REST.serializers import DealSerializer
from rest_framework import status
from rest_framework.authtoken.models import Token


class RewardsAPI(APIView):

    """
    GET (Get your user) - Required params: none

    """

    authentication_classes = (authentication.TokenAuthentication,)

    def get(self, request, format=None):
        response = {}
        auth_token = request.auth
        token = Token.objects.get(key=auth_token)
        latitude = float(request.QUERY_PARAMS['latitude'])
        longitude = float(request.QUERY_PARAMS['longitude'])
        unlocked_deals, locked_deals = get_nearby_rewards(token.user, latitude, longitude)
        response['unlocked_deals'] = DealSerializer(unlocked_deals, many=True).data
        response['locked_deals'] = DealSerializer(locked_deals, many=True).data
        return Response(response, status=status.HTTP_200_OK)

    def post(self, request, format=None):
        response = {}
        auth_token = request.auth
        token = Token.objects.get(key=auth_token)
        rewards_added = add_points(token.user, request.DATA)
        print "Referral Reward Added:" + str(rewards_added)
        return Response(response, status=status.HTTP_200_OK)