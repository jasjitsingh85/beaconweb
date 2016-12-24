from django.contrib.auth.models import User
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import authentication
from rest_framework.authtoken.models import Token
from beaconWeb.apps.beacon.common.utils.location import *
from rest_framework import status
from beaconWeb.REST.serializers import BeaconWithFollowersSerializer

class LocationAPI(APIView):
    """
    Location
    POST - Required params: latitude, longitude
    latitude -- Current user latitude
    longitude -- Current user longitude
    """

    authentication_classes = (authentication.TokenAuthentication,)

    def post(self, request, format=None):
        response = {}
        auth_token = request.auth
        try:
            token = Token.objects.get(key=auth_token)
        except Token.DoesNotExist:
            token = None
        if token is not None:
            user = token.user
            lat = float(request.DATA['latitude'])
            long = float(request.DATA['longitude'])
            if set_location(user, lat, long):
                is_here = check_if_here(user, lat, long)
                serializer = BeaconWithFollowersSerializer(is_here, many=True)
                response['isHere'] = serializer.data
                return Response(response, status=status.HTTP_200_OK)
            else:
                response['message'] = "Failed to set location"
                return Response(response, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            response['message'] = "No user associated with token found"
            return Response(response, status=status.HTTP_401_UNAUTHORIZED)