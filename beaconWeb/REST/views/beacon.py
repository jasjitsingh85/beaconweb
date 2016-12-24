from django.conf import settings
from django.contrib.auth.models import User
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import authentication
from rest_framework.authtoken.models import Token
from beaconWeb.apps.beacon.common.utils.hotspot import *
from rest_framework import status
from beaconWeb.REST.serializers import BeaconWithFollowersSerializer
from beaconWeb.REST.serializers import BeaconMobileSerializer
from beaconWeb.REST.serializers import BeaconSerializer


class BeaconAPI(APIView):
    """
    Beacon operations
    POST (Create your Hotspot) - Required params: description, time, latitude, longitude
    GET (Get your Hotspot) - Required params: none

    """

    authentication_classes = (authentication.TokenAuthentication,)

    def post(self, request, format=None):
        response = {}
        auth_token = request.auth
        if Token.objects.filter(key=auth_token).exists():
            token = Token.objects.get(key=auth_token)
            user = User.objects.get(username=token.user.username)
            invite_list = request.DATA.getlist('invite_list[]')
            beacon = create_beacon(user, request.DATA, invite_list)
            serializer = BeaconSerializer(beacon)
            response['beacon'] = serializer.data
            return Response(response, status=status.HTTP_200_OK)
        else:
            response['message'] = "No user associated with token found"
            return Response(response, status=status.HTTP_401_UNAUTHORIZED)

    def get(self, request, format=None):
        response = {}
        auth_token = request.auth
        if str(auth_token) == settings.MOBILE_VIEW_TOKEN:
            beacon = get_hotspot_for_mobile_view(request.QUERY_PARAMS)
            if beacon is not False:
                serializer = BeaconMobileSerializer(beacon)
                response['beacon'] = serializer.data
                return Response(response, status=status.HTTP_200_OK)
            else:
                response['message'] = "Beacon is expired"
                return Response(response, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        elif Token.objects.filter(key=auth_token).exists():
            beacon_id = request.QUERY_PARAMS['beacon_id']
            beacon = get_hotspot(beacon_id)
            serializer = BeaconWithFollowersSerializer(beacon)
            response['beacon'] = serializer.data
            return Response(response, status=status.HTTP_200_OK)
        else:
            response['message'] = "No user associated with token found"
            return Response(response, status=status.HTTP_401_UNAUTHORIZED)
