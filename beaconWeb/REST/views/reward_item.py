from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import authentication
from beaconWeb.apps.beacon.models.deal import Deal
from beaconWeb.apps.beacon.common.utils.rewards import add_reward_items_for_referral, authorize_reward_item
from beaconWeb.REST.serializers import RewardsSerializer
from rest_framework import status
from rest_framework.authtoken.models import Token
from django.contrib.auth.models import User


class RewardItemAPI(APIView):

    """
    GET (Get your user) - Required params: none

    """

    authentication_classes = (authentication.TokenAuthentication,)

    def get(self, request, format=None):
        response = {}
        user = Token.objects.get(key=request.auth).user
        response['number_of_reward_items'] = user.profile.number_of_reward_items
        return Response(response, status=status.HTTP_200_OK)

    def post(self, request, format=None):
        response = {}
        user = Token.objects.get(key=request.auth).user
        if 'referring_user' not in request.DATA:
            return False
        referring_user = User.objects.get(username=request.DATA['referring_user'])
        add_reward_items_for_referral(user, referring_user)
        response['number_of_reward_items'] = user.profile.number_of_reward_items
        return Response(response, status=status.HTTP_200_OK)

    def put(self, request, format=None):
        response = {}
        user = Token.objects.get(key=request.auth).user
        authorize_reward_item(user, request.DATA)
        response['number_of_reward_items'] = user.profile.number_of_reward_items
        return Response(response, status=status.HTTP_200_OK)
