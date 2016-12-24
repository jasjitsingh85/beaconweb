from django.conf import settings
from django.contrib.auth.models import User
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import authentication
from rest_framework.authtoken.models import Token
from beaconWeb.apps.beacon.common.utils.hotspot import *
from rest_framework import status
from beaconWeb.REST.serializers import BeaconWithDealStatusSerializer
from beaconWeb.REST.serializers import BeaconMobileSerializer
from beaconWeb.REST.serializers import BeaconSerializer


class HotspotAPI(APIView):
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
            data = request.DATA
            invite_list = data.getlist('invite_list[]')
            time = datetime.fromtimestamp(float(data['time']))
            latitude = float(data['latitude'])
            longitude = float(data['longitude'])
            address = data['address']
            description = data['description']
            user_latitude = data.get('user_latitude')
            if user_latitude:
                user_latitude = float(user_latitude)
            user_longitude = data.get('user_longitude')
            if user_longitude:
                user_longitude = float(user_longitude)
            beacon = create_hotspot(token.user, latitude, longitude, address, description, time, invite_list, user_latitude, user_longitude)
            serializer = BeaconWithDealStatusSerializer(beacon)
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
            serializer = BeaconWithDealStatusSerializer(beacon)
            response['beacon'] = serializer.data
            return Response(response, status=status.HTTP_200_OK)
        else:
            response['message'] = "No user associated with token found"
            return Response(response, status=status.HTTP_401_UNAUTHORIZED)

    def put(self, request, format=None):
        response = {}
        auth_token = request.auth
        if Token.objects.filter(key=auth_token).exists():
            token = Token.objects.get(key=auth_token)
            beacon = change_hotspot(token.user, request.DATA)
            serializer = BeaconWithDealStatusSerializer(beacon)
            response['beacon'] = serializer.data
            return Response(response, status=status.HTTP_200_OK)
        else:
            response['message'] = "No user associated with token found"
            return Response(response, status=status.HTTP_401_UNAUTHORIZED)
