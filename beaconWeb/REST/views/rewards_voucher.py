from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import authentication
from beaconWeb.apps.beacon.models.deal import Deal
from beaconWeb.apps.beacon.common.utils.rewards import get_active_vouchers, purchase_reward_item, redeem_reward
from beaconWeb.REST.serializers import RewardsSerializer
from rest_framework import status
from rest_framework.authtoken.models import Token


class RewardsVoucherAPI(APIView):

    """
    GET (Get your user) - Required params: none

    """

    authentication_classes = (authentication.TokenAuthentication,)

    def get(self, request, format=None):
        response = {}
        user = Token.objects.get(key=request.auth).user
        response['total_rewards'] = user.profile.reward_score
        active_vouchers = get_active_vouchers(user)
        serializer = RewardsSerializer(active_vouchers, many=True)
        response['vouchers'] = serializer.data
        return Response(response, status=status.HTTP_200_OK)

    def post(self, request, format=None):
        response = {}
        user = Token.objects.get(key=request.auth).user
        purchase_reward_item(user, request.DATA)
        response['total_rewards'] = user.profile.reward_score
        return Response(response, status=status.HTTP_200_OK)

    def put(self, request, format=None):
        response = {}
        redeem_reward(request.DATA)
        return Response(response, status=status.HTTP_200_OK)