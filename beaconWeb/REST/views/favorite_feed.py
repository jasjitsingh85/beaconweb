from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import authentication
from rest_framework import status
from rest_framework.authtoken.models import Token
from beaconWeb.apps.beacon.common.utils.favorite_feed import get_favorite_feed, follow_or_unfollow_favorite, add_time_feed_viewed
from beaconWeb.REST.serializers import FavoriteFeedSerializer, EventsSerializer
from beaconWeb.apps.beacon.common.utils.events import get_events_for_user
import time
import datetime


class FavoriteFeedAPI(APIView):

    authentication_classes = (authentication.TokenAuthentication,)

    def get(self, request, format=None):
        response = {}
        auth_token = request.auth
        token = Token.objects.get(key=auth_token)
        t0 = time.time()
        response['favorite_feed'] = get_favorite_feed(token.user)
        # response['suggested'] = get_suggested_places(token.user)
        t1 = time.time()
        print "Favorite Feed Time: " + str(t1 - t0)
        events = get_events_for_user(token.user)
        response['events'] = EventsSerializer(events, many=True).data
        return Response(response, status=status.HTTP_200_OK)

    def put(self, request, format=None):
        response = {}
        auth_token = request.auth
        token = Token.objects.get(key=auth_token)
        add_time_feed_viewed(token.user, request.DATA)
        print "Timestamp Sent: " + str(request.DATA['timestamp'])
        return Response(response, status=status.HTTP_200_OK)

    def post(self, request, format=None):
        response = {}
        auth_token = request.auth
        token = Token.objects.get(key=auth_token)
        response["is_favorited"] = follow_or_unfollow_favorite(token.user, request.DATA)
        return Response(response, status=status.HTTP_200_OK)