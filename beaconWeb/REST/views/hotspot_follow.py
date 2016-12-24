from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import authentication
from rest_framework.authtoken.models import Token
from beaconWeb.apps.beacon.common.utils.hotspot_follow import *
from beaconWeb.REST.serializers import BeaconSerializer
from rest_framework import status
from django.conf import settings
from beaconWeb.REST.serializers import BeaconWithFollowersSerializer
from beaconWeb.REST.serializers import BeaconWithDealStatusSerializer
import time


class HotspotFollowAPI(APIView):
    """
    This is what you post to when someone says "Yes" to going. GET gives you a list of hotspots
    you've created or been invited to
    POST (Follow/un-follow a beacon) - Required params: beacon_id, follow (true/false)
    beacon_id -- ID of beacon (each deal also has an associated beacon)
    follow -- true or false (true if person is going, false if they are not)

    GET (Get list of beacons you can follow) - Required params: none

    """

    authentication_classes = (authentication.TokenAuthentication,)

    def post(self, request, format=None):
        response = {}
        auth_token = request.auth
        if str(auth_token) == settings.MOBILE_VIEW_TOKEN:
            invite_id = request.DATA["inviteId"]
            mobileview_hotspot_follow(invite_id)
            return Response(response, status=status.HTTP_200_OK)
        elif Token.objects.filter(key=auth_token).exists():
            token = Token.objects.get(key=auth_token)
            beacon = follow_hotspot(token.user, request.DATA)
            serializer = BeaconSerializer(beacon)
            response['beacon'] = serializer.data
            return Response(response, status=status.HTTP_200_OK)
        else:
            response['message'] = "No user associated with token found"
            return Response(response, status=status.HTTP_401_UNAUTHORIZED)

    def get(self, request, format=None):
        response = {}
        auth_token = request.auth
        if Token.objects.filter(key=auth_token).exists():
            token = Token.objects.get(key=auth_token)
            hotspots = get_hotspot_list(token.user)
            serializer = BeaconWithDealStatusSerializer(hotspots, many=True)
            return Response(serializer.data)
        else:
            response['message'] = "No user associated with token found"
            return Response(response, status=status.HTTP_401_UNAUTHORIZED)