from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import authentication
from rest_framework.authtoken.models import Token
from beaconWeb.apps.beacon.common.utils.friends import *
import time
from django_rq import job
from django.conf import settings
from rest_framework import status
from beaconWeb.REST.serializers import UserSerializer


class FriendManageAPI(APIView):
    """
    """

    authentication_classes = (authentication.TokenAuthentication,)

    def get(self, request, format=None):
        response = {}
        auth_token = request.auth
        if Token.objects.filter(key=auth_token).exists():
            token = Token.objects.get(key=auth_token)
            t0 = time.time()
            approved_friends, blocked_friends = get_friends_and_removed_friends_list(token.user)
            t1 = time.time()
            print "Friends + Removed Friends: " + str(t1-t0)
            approved_friends = UserSerializer(approved_friends, many=True)
            blocked_friends = UserSerializer(blocked_friends, many=True)
            response['friends'] = approved_friends.data
            response['removed_friends'] = blocked_friends.data
            return Response(response, status.HTTP_200_OK)
        else:
            response['message'] = "No user associated with token found"
            return Response(response, status=status.HTTP_401_UNAUTHORIZED)

    def post(self, request, format=None):
        response = {}
        auth_token = request.auth
        if Token.objects.filter(key=auth_token).exists():
            token = Token.objects.get(key=auth_token)
            response['friend_status'] = toggle_blocking_of_friend(token.user, request.DATA)
            return Response(response, status.HTTP_200_OK)
        else:
            response['message'] = "No user associated with token found"
            return Response(response, status=status.HTTP_401_UNAUTHORIZED)