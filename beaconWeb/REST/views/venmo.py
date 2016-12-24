from rest_framework.views import APIView
from rest_framework import status
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from rest_framework import permissions
from beaconWeb.apps.beacon.models import Profile
from beaconWeb.REST.serializers import ProfileSerializer
from django.contrib.auth.models import User
from beaconWeb.apps.beacon.common.common_utils import add_venmo_token_for_user
import time
from beaconWeb.settings import VENMO_CLIENT_ID, VENMO_SECRET_ID
import requests


class VenmoOAuthAPI(APIView):

    permission_classes = (permissions.AllowAny,)

    def get(self, request):
        response = {}
        code = request.QUERY_PARAMS['code']
        user_id = request.QUERY_PARAMS['user_id']
        data = {
            "client_id": VENMO_CLIENT_ID,
            "client_secret": VENMO_SECRET_ID,
            "code": code
        }
        url = "https://api.venmo.com/v1/oauth/access_token"
        response = requests.post(url, data)
        response_dict = response.json()
        add_venmo_token_for_user(user_id, response_dict['access_token'])
        return Response(response, status=status.HTTP_200_OK)