from django.contrib.auth.models import User
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import authentication
from rest_framework.authtoken.models import Token
from rest_framework import status
from beaconWeb.apps.beacon.common.common_utils import get_venue_recommendations


class RecommendationAPI(APIView):
    """
    Beacon operations
    POST (Create your Hotspot) - Required params: description, time, latitude, longitude
    GET (Get your Hotspot) - Required params: none

    """

    authentication_classes = (authentication.TokenAuthentication,)

    def get(self, request, format=None):
        response = {}
        user = Token.objects.get(key=request.auth).user
        response['recommendations'] = get_venue_recommendations(user)
        return Response(response, status=status.HTTP_200_OK)