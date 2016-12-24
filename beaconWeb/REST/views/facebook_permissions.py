from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import authentication
from rest_framework import status
from rest_framework.authtoken.models import Token
from beaconWeb.apps.beacon.common.utils.user_profile import add_or_update_facebook_access_token
from beaconWeb.apps.beacon.common.utils.favorite_feed import get_favorite_feed, follow_or_unfollow_favorite, add_time_feed_viewed
from beaconWeb.REST.serializers import FavoriteFeedSerializer, EventsSerializer
from beaconWeb.apps.beacon.common.utils.events import get_events_for_user
import time
import datetime


class FacebookPermissionsAPI(APIView):

    authentication_classes = (authentication.TokenAuthentication,)

    def post(self, request, format=None):
        response = {}
        auth_token = request.auth
        token = Token.objects.get(key=auth_token)
        response['message'] = add_or_update_facebook_access_token(token.user, request.DATA)
        return Response(response, status=status.HTTP_200_OK)